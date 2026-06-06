from pydantic import BaseModel, ConfigDict
from datetime import datetime


class WalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    balance: float
    currency: str
    locked_amount: float


class WalletTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    amount: float
    reference: str
    description: str
    created_at: datetime
