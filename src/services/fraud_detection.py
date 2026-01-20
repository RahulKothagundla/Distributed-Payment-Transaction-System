from src.utils.redis_client import redis_client
from src.config import get_settings

settings = get_settings()

class FraudDetectionService:
    @staticmethod
    def calculate_fraud_score(user_id: str, amount: float) -> float:
        """Calculate fraud risk score (0-100)"""
        # Check cache first
        cached_score = redis_client.get_cached_fraud_score(user_id)
        if cached_score is not None:
            return cached_score
        
        score = 0.0
        
        # Rule 1: Amount threshold
        if amount > settings.fraud_threshold:
            score += 40.0
        
        # Rule 2: Daily transaction frequency
        daily_count = redis_client.get_daily_transaction_count(user_id)
        if daily_count > settings.max_daily_transactions:
            score += 30.0
        
        # Rule 3: Velocity check (simplified)
        if amount > 10000:
            score += 30.0
        
        # Cache the score
        redis_client.cache_fraud_score(user_id, score)
        
        return min(score, 100.0)
    
    @staticmethod
    def should_block_transaction(fraud_score: float) -> bool:
        """Determine if transaction should be blocked"""
        return fraud_score >= 70.0