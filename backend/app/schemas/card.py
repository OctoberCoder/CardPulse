from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DenominationResponse(BaseModel):
    id: int
    value: float
    currency: str
    active: bool

    class Config:
        from_attributes = True


class CardBrandResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    icon: str
    active: bool
    denominations: list[DenominationResponse] = []

    class Config:
        from_attributes = True


class CardBrandCreate(BaseModel):
    name: str
    slug: str
    description: str = ""
    icon: str = ""


class CardSubmissionResponse(BaseModel):
    id: int
    brand_id: int
    denomination_id: int
    quoted_amount: float
    final_amount: Optional[float] = None
    status: str
    admin_notes: str
    submitted_at: datetime

    class Config:
        from_attributes = True


class CardQuoteRequest(BaseModel):
    brand_id: int
    denomination_id: int
    card_code: str


class CardQuoteResponse(BaseModel):
    quoted_amount: float
    buy_rate: float


class CardSubmitRequest(BaseModel):
    brand_id: int
    denomination_id: int
    card_code: str
    quoted_amount: float
    card_image_url: str = ""
