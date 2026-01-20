from sqlalchemy.orm import Session
from src.models.transaction import Transaction, TransactionStatus
from src.services.fraud_detection import FraudDetectionService
from src.services.webhook_service import WebhookService
from src.models.webhook import WebhookPayload
from src.utils.redis_client import redis_client
from src.utils.kafka_producer import kafka_producer
from datetime import datetime
from typing import Optional

class PaymentService:
    @staticmethod
    def create_transaction(
        db: Session,
        idempotency_key: str,
        user_id: str,
        amount: float,
        currency: str = "USD",
        description: Optional[str] = None,
        webhook_url: Optional[str] = None
    ) -> Transaction:
        """Create new transaction with idempotency check"""
        
        # Check idempotency - prevent duplicate transactions
        existing = db.query(Transaction).filter(
            Transaction.idempotency_key == idempotency_key
        ).first()
        
        if existing:
            return existing
        
        # Acquire distributed lock
        lock_acquired = redis_client.acquire_lock(f"txn:{idempotency_key}")
        if not lock_acquired:
            raise ValueError("Unable to acquire lock for transaction")
        
        try:
            # Calculate fraud score
            fraud_score = FraudDetectionService.calculate_fraud_score(user_id, amount)
            
            # Create transaction
            transaction = Transaction(
                idempotency_key=idempotency_key,
                user_id=user_id,
                amount=amount,
                currency=currency,
                description=description,
                fraud_score=fraud_score,
                webhook_url=webhook_url,
                status=TransactionStatus.PENDING
            )
            
            # Block if high fraud score
            if FraudDetectionService.should_block_transaction(fraud_score):
                transaction.status = TransactionStatus.FAILED
            
            db.add(transaction)
            db.commit()
            db.refresh(transaction)
            
            # Increment daily transaction count
            redis_client.increment_daily_transactions(user_id)
            
            # Send Kafka event
            kafka_producer.send_payment_event("transaction.created", {
                "id": transaction.id,
                "user_id": transaction.user_id,
                "amount": transaction.amount,
                "status": transaction.status.value,
                "created_at": transaction.created_at.isoformat()
            })
            
            return transaction
            
        finally:
            redis_client.release_lock(f"txn:{idempotency_key}")
    
    @staticmethod
    async def process_transaction(db: Session, transaction_id: str) -> Transaction:
        """Process pending transaction"""
        transaction = db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()
        
        if not transaction:
            raise ValueError("Transaction not found")
        
        if transaction.status != TransactionStatus.PENDING:
            return transaction
        
        # Update status to processing
        transaction.status = TransactionStatus.PROCESSING
        db.commit()
        
        # Simulate payment processing logic
        # In production, this would call payment gateway API
        try:
            # Payment gateway logic here
            transaction.status = TransactionStatus.COMPLETED
        except Exception:
            transaction.status = TransactionStatus.FAILED
        
        transaction.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(transaction)
        
        # Send webhook notification
        if transaction.webhook_url:
            webhook_payload = WebhookPayload(
                event_type="transaction.completed" if transaction.status == TransactionStatus.COMPLETED else "transaction.failed",
                transaction_id=transaction.id,
                status=transaction.status.value,
                amount=transaction.amount,
                currency=transaction.currency,
                timestamp=datetime.utcnow()
            )
            
            webhook_delivered = await WebhookService.send_webhook(
                transaction.webhook_url,
                webhook_payload
            )
            transaction.webhook_delivered = "true" if webhook_delivered else "false"
            db.commit()
        
        return transaction