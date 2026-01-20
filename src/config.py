from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://payment_user:payment_pass@localhost:5432/payment_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_ttl: int = 300  # 5 minutes
    
    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "payment-events"
    
    # Application
    app_name: str = "Distributed Payment System"
    app_version: str = "1.0.0"
    secret_key: str = "your-secret-key"
    debug: bool = True
    
    # Fraud Detection
    fraud_threshold: float = 5000.0  # Amount threshold for fraud check
    max_daily_transactions: int = 10
    
    # Webhook
    webhook_secret: str = "webhook-secret"
    webhook_timeout: int = 5
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()