from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, Float, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base


class CardSubmissionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class CardBrand(Base):
    __tablename__ = "card_brands"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    icon: Mapped[str] = mapped_column(String(255), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    denominations: Mapped[list["Denomination"]] = relationship(back_populates="brand", cascade="all, delete-orphan")


class Denomination(Base):
    __tablename__ = "denominations"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("card_brands.id"))
    value: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    brand: Mapped["CardBrand"] = relationship(back_populates="denominations")


class CardSubmission(Base):
    __tablename__ = "card_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    brand_id: Mapped[int] = mapped_column(ForeignKey("card_brands.id"))
    denomination_id: Mapped[int] = mapped_column(ForeignKey("denominations.id"))
    card_code: Mapped[str] = mapped_column(Text)
    card_image_url: Mapped[str] = mapped_column(String(500), default="")
    quoted_amount: Mapped[float] = mapped_column(Float)
    final_amount: Mapped[float] = mapped_column(Float, nullable=True)
    status: Mapped[CardSubmissionStatus] = mapped_column(
        SAEnum(CardSubmissionStatus), default=CardSubmissionStatus.PENDING
    )
    reviewed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    admin_notes: Mapped[str] = mapped_column(Text, default="")
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    brand = relationship("CardBrand")
    denomination = relationship("Denomination")
