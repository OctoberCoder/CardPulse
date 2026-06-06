from datetime import datetime
from sqlalchemy import String, Float, DateTime, func, ForeignKey, Boolean, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base


class ReloadlyTransactionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class ReloadlyProduct(Base):
    __tablename__ = "reloadly_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    reloadly_id: Mapped[int] = mapped_column(unique=True)
    brand: Mapped[str] = mapped_column(String(100))
    denomination: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    sell_price: Mapped[float] = mapped_column(Float)
    fee: Mapped[float] = mapped_column(Float, default=0.0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_synced: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReloadlyTransaction(Base):
    __tablename__ = "reloadly_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("reloadly_products.id"))
    order_reference: Mapped[str] = mapped_column(String(255), unique=True)
    amount: Mapped[float] = mapped_column(Float)
    fee: Mapped[float] = mapped_column(Float, default=0.0)
    recipient_email: Mapped[str] = mapped_column(String(255))
    status: Mapped[ReloadlyTransactionStatus] = mapped_column(
        SAEnum(ReloadlyTransactionStatus), default=ReloadlyTransactionStatus.PENDING
    )
    reloadly_tx_id: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    product = relationship("ReloadlyProduct")
