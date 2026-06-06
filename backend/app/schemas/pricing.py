from pydantic import BaseModel, ConfigDict
from typing import Optional


class RateAdjustmentCreate(BaseModel):
    trigger_type: str
    operator: str = "add"
    value: float
    adjustment_pct: float
    priority: int = 0


class RateAdjustmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    trigger_type: str
    operator: str
    value: float
    adjustment_pct: float
    priority: int
    active: bool


class RateRuleCreate(BaseModel):
    brand_id: int
    denomination_id: int
    base_buy_rate: float
    sell_markup_pct: float = 0.10
    min_rate: float = 0.50
    max_rate: float = 0.95
    adjustments: list[RateAdjustmentCreate] = []


class RateRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    brand_id: int
    denomination_id: int
    base_buy_rate: float
    sell_markup_pct: float
    min_rate: float
    max_rate: float
    active: bool
    adjustments: list[RateAdjustmentResponse] = []


class EffectiveRateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    brand_id: int
    denomination_id: int
    base_buy_rate: float
    effective_buy_rate: float
    sell_price: float
