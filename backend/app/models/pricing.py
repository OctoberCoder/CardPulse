from datetime import datetime
from sqlalchemy import String, Float, DateTime, func, ForeignKey, Boolean, Integer, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base


class TriggerType(str, enum.Enum):
    STOCK_LOW = "stock_low"
    STOCK_HIGH = "stock_high"
    SUBMISSION_VOLUME_HIGH = "submission_volume_high"
    DAY_OF_WEEK = "day_of_week"


class RateRule(Base):
    __tablename__ = "rate_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("card_brands.id"))
    denomination_id: Mapped[int] = mapped_column(ForeignKey("denominations.id"))
    base_buy_rate: Mapped[float] = mapped_column(Float)
    sell_markup_pct: Mapped[float] = mapped_column(Float, default=0.10)
    min_rate: Mapped[float] = mapped_column(Float, default=0.50)
    max_rate: Mapped[float] = mapped_column(Float, default=0.95)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    brand = relationship("CardBrand")
    denomination = relationship("Denomination")
    adjustments: Mapped[list["RateAdjustment"]] = relationship(back_populates="rule", cascade="all, delete-orphan")


class RateAdjustment(Base):
    __tablename__ = "rate_adjustments"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("rate_rules.id"))
    trigger_type: Mapped[TriggerType] = mapped_column(SAEnum(TriggerType))
    operator: Mapped[str] = mapped_column(String(10), default="add")
    value: Mapped[float] = mapped_column(Float)
    adjustment_pct: Mapped[float] = mapped_column(Float)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    rule: Mapped["RateRule"] = relationship(back_populates="adjustments")


class RateSnapshot(Base):
    __tablename__ = "rate_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("card_brands.id"))
    denomination_id: Mapped[int] = mapped_column(ForeignKey("denominations.id"))
    effective_buy_rate: Mapped[float] = mapped_column(Float)
    effective_sell_price: Mapped[float] = mapped_column(Float)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
