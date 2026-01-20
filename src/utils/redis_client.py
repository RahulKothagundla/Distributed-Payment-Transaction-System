import redis
from typing import Optional
from src.config import get_settings

settings = get_settings()

class RedisClient:
    def __init__(self):
        self.client = redis.from_url(settings.redis_url, decode_responses=True)
    
    def acquire_lock(self, key: str, timeout: int = 10) -> bool:
        """Acquire distributed lock using Redis"""
        lock_key = f"lock:{key}"
        return self.client.set(lock_key, "1", nx=True, ex=timeout)
    
    def release_lock(self, key: str) -> None:
        """Release distributed lock"""
        lock_key = f"lock:{key}"
        self.client.delete(lock_key)
    
    def get_cached_fraud_score(self, user_id: str) -> Optional[float]:
        """Get cached fraud score for user"""
        key = f"fraud_score:{user_id}"
        score = self.client.get(key)
        return float(score) if score else None
    
    def cache_fraud_score(self, user_id: str, score: float) -> None:
        """Cache fraud score with TTL"""
        key = f"fraud_score:{user_id}"
        self.client.setex(key, settings.redis_ttl, str(score))
    
    def increment_daily_transactions(self, user_id: str) -> int:
        """Increment and return daily transaction count"""
        key = f"daily_txn:{user_id}"
        count = self.client.incr(key)
        if count == 1:
            # Set expiry for 24 hours on first transaction
            self.client.expire(key, 86400)
        return count
    
    def get_daily_transaction_count(self, user_id: str) -> int:
        """Get current daily transaction count"""
        key = f"daily_txn:{user_id}"
        count = self.client.get(key)
        return int(count) if count else 0

redis_client = RedisClient()