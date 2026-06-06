from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from .base import Base


class FraudSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FraudAlertStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATED = "investigated"
    RESOLVED = "resolved"


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    triggered_by_rule: Mapped[str] = mapped_column(String(100))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    submission_id: Mapped[int] = mapped_column(ForeignKey("card_submissions.id"), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[FraudSeverity] = mapped_column(SAEnum(FraudSeverity))
    status: Mapped[FraudAlertStatus] = mapped_column(SAEnum(FraudAlertStatus), default=FraudAlertStatus.OPEN)
    resolved_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
