from kafka import KafkaProducer
import json
from src.config import get_settings

settings = get_settings()

class PaymentEventProducer:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    
    def send_payment_event(self, event_type: str, transaction_data: dict) -> None:
        """Send payment event to Kafka topic"""
        event = {
            "event_type": event_type,
            "transaction": transaction_data,
            "timestamp": transaction_data.get("created_at")
        }
        self.producer.send(settings.kafka_topic, event)
        self.producer.flush()
    
    def close(self):
        self.producer.close()

kafka_producer = PaymentEventProducer()