from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class OrderCreate(BaseModel):
    source: str
    listing_id: int
    payment_method: str
    idempotency_key: Optional[str] = None


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source: str
    amount_paid: float
    fee: float
    status: str
    payment_method: str
    payment_reference: str
    created_at: datetime
