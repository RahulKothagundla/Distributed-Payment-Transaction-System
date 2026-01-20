import pytest
from src.services.fraud_detection import FraudDetectionService

def test_fraud_score_low_amount():
    """Test fraud score for normal transaction"""
    score = FraudDetectionService.calculate_fraud_score("user_123", 100.0)
    assert score < 70.0

def test_fraud_score_high_amount():
    """Test fraud score for high-value transaction"""
    score = FraudDetectionService.calculate_fraud_score("user_456", 15000.0)
    assert score >= 70.0

def test_should_block_high_risk():
    """Test blocking high-risk transactions"""
    assert FraudDetectionService.should_block_transaction(80.0) == True
    assert FraudDetectionService.should_block_transaction(50.0) == False