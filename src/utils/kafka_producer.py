from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
import logging
from src.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class PaymentEventProducer:
    def __init__(self):
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                request_timeout_ms=1000,  # 1 second timeout
                max_block_ms=1000  # Don't block for more than 1 second
            )
            self.available = True
            logger.info("Kafka producer initialized successfully")
        except Exception as e:
            logger.warning(f"Kafka unavailable, events will not be sent: {e}")
            self.producer = None
            self.available = False
    
    def send_payment_event(self, event_type: str, transaction_data: dict) -> None:
        """Send payment event to Kafka topic (gracefully fails if Kafka unavailable)"""
        if not self.available or self.producer is None:
            logger.debug(f"Skipping Kafka event (Kafka unavailable): {event_type}")
            return
        
        try:
            event = {
                "event_type": event_type,
                "transaction": transaction_data,
                "timestamp": transaction_data.get("created_at")
            }
            self.producer.send(settings.kafka_topic, event)
            self.producer.flush(timeout=1)  # 1 second timeout
            logger.debug(f"Sent Kafka event: {event_type}")
        except KafkaError as e:
            logger.warning(f"Failed to send Kafka event: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error sending Kafka event: {e}")
    
    def close(self):
        if self.producer:
            try:
                self.producer.close(timeout=2)
            except Exception:
                pass

kafka_producer = PaymentEventProducer()