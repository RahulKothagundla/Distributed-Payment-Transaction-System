from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from src.models.transaction import Transaction, TransactionStatus
from src.services.payment_service import PaymentService
from src.main import get_db
import uuid

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])

class CreateTransactionRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(default="USD", description="Currency code")
    description: Optional[str] = Field(None, description="Transaction description")
    webhook_url: Optional[str] = Field(None, description="Webhook callback URL")

class TransactionResponse(BaseModel):
    id: str
    idempotency_key: str
    user_id: str
    amount: float
    currency: str
    status: str
    fraud_score: float
    created_at: str
    
    class Config:
        from_attributes = True

@router.post("/", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    request: CreateTransactionRequest,
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="X-Idempotency-Key")
):
    """Create new payment transaction with idempotency protection"""
    try:
        transaction = PaymentService.create_transaction(
            db=db,
            idempotency_key=idempotency_key,
            user_id=request.user_id,
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            webhook_url=request.webhook_url
        )
        
        return TransactionResponse(
            id=transaction.id,
            idempotency_key=transaction.idempotency_key,
            user_id=transaction.user_id,
            amount=transaction.amount,
            currency=transaction.currency,
            status=transaction.status.value,
            fraud_score=transaction.fraud_score,
            created_at=transaction.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{transaction_id}/process", response_model=TransactionResponse)
async def process_transaction(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """Process a pending transaction"""
    try:
        transaction = await PaymentService.process_transaction(db, transaction_id)
        return TransactionResponse(
            id=transaction.id,
            idempotency_key=transaction.idempotency_key,
            user_id=transaction.user_id,
            amount=transaction.amount,
            currency=transaction.currency,
            status=transaction.status.value,
            fraud_score=transaction.fraud_score,
            created_at=transaction.created_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """Get transaction by ID"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return TransactionResponse(
        id=transaction.id,
        idempotency_key=transaction.idempotency_key,
        user_id=transaction.user_id,
        amount=transaction.amount,
        currency=transaction.currency,
        status=transaction.status.value,
        fraud_score=transaction.fraud_score,
        created_at=transaction.created_at.isoformat()
    )

@router.get("/", response_model=List[TransactionResponse])
async def list_transactions(
    user_id: Optional[str] = None,
    status: Optional[TransactionStatus] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """List transactions with optional filters"""
    query = db.query(Transaction)
    
    if user_id:
        query = query.filter(Transaction.user_id == user_id)
    if status:
        query = query.filter(Transaction.status == status)
    
    transactions = query.order_by(Transaction.created_at.desc()).limit(limit).all()
    
    return [
        TransactionResponse(
            id=t.id,
            idempotency_key=t.idempotency_key,
            user_id=t.user_id,
            amount=t.amount,
            currency=t.currency,
            status=t.status.value,
            fraud_score=t.fraud_score,
            created_at=t.created_at.isoformat()
        )
        for t in transactions
    ]