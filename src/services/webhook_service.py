import httpx
import hmac
import hashlib
from src.models.webhook import WebhookPayload
from src.config import get_settings

settings = get_settings()

class WebhookService:
    @staticmethod
    def generate_signature(payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook"""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    async def send_webhook(url: str, payload: WebhookPayload) -> bool:
        """Send webhook notification with signature"""
        try:
            payload_json = payload.model_dump_json()
            signature = WebhookService.generate_signature(
                payload_json, 
                settings.webhook_secret
            )
            
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature
            }
            
            async with httpx.AsyncClient(timeout=settings.webhook_timeout) as client:
                response = await client.post(url, content=payload_json, headers=headers)
                return response.status_code == 200
        except Exception:
            return False