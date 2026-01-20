import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.main import app, get_db
from src.models.transaction import Base
import uuid

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_create_transaction():
    """Test creating a new transaction"""
    idempotency_key = str(uuid.uuid4())
    response = client.post(
        "/api/v1/transactions/",
        json={
            "user_id": "user_123",
            "amount": 100.0,
            "currency": "USD",
            "description": "Test payment"
        },
        headers={"X-Idempotency-Key": idempotency_key}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 100.0
    assert data["status"] == "pending"

def test_idempotency():
    """Test idempotency key prevents duplicates"""
    idempotency_key = str(uuid.uuid4())
    
    # First request
    response1 = client.post(
        "/api/v1/transactions/",
        json={"user_id": "user_123", "amount": 50.0},
        headers={"X-Idempotency-Key": idempotency_key}
    )
    
    # Second request with same key
    response2 = client.post(
        "/api/v1/transactions/",
        json={"user_id": "user_123", "amount": 50.0},
        headers={"X-Idempotency-Key": idempotency_key}
    )
    
    assert response1.status_code == 201
    assert response2.status_code == 201
    assert response1.json()["id"] == response2.json()["id"]

def test_get_transaction():
    """Test retrieving transaction by ID"""
    # Create transaction first
    idempotency_key = str(uuid.uuid4())
    create_response = client.post(
        "/api/v1/transactions/",
        json={"user_id": "user_123", "amount": 75.0},
        headers={"X-Idempotency-Key": idempotency_key}
    )
    transaction_id = create_response.json()["id"]
    
    # Get transaction
    response = client.get(f"/api/v1/transactions/{transaction_id}")
    assert response.status_code == 200
    assert response.json()["id"] == transaction_id

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"