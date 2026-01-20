from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class WebhookPayload(BaseModel):
    event_type: str
    transaction_id: str
    status: str
    amount: float
    currency: str
    timestamp: datetime
    
class WebhookRequest(BaseModel):
    url: HttpUrl
    payload: WebhookPayload
    secret: str