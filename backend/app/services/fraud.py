from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fraud import FraudAlert, FraudSeverity
from app.models.card import CardSubmission


async def check_card_submission(
    db: AsyncSession,
    user_id: int,
    card_code: str,
    brand_id: int,
) -> list[FraudAlert]:
    alerts: list[FraudAlert] = []

    # Rule 1: Duplicate card code
    result = await db.execute(
        select(CardSubmission).where(CardSubmission.card_code == card_code)
    )
    existing = result.scalars().all()
    if len(existing) > 1 or (len(existing) == 1 and existing[0].user_id != user_id):
        alert = FraudAlert(
            triggered_by_rule="duplicate_code",
            user_id=user_id, submission_id=None,
            description="Duplicate card code detected across accounts",
            severity=FraudSeverity.HIGH,
        )
        db.add(alert)
        alerts.append(alert)

    # Rule 2: Velocity check — more than 5 submissions in 1 hour
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    count = await db.execute(
        select(func.count()).select_from(CardSubmission)
        .where(CardSubmission.user_id == user_id, CardSubmission.submitted_at >= since)
    )
    if (count.scalar() or 0) >= 5:
        alert = FraudAlert(
            triggered_by_rule="velocity_high",
            user_id=user_id, submission_id=None,
            description="More than 5 submissions in 1 hour",
            severity=FraudSeverity.MEDIUM,
        )
        db.add(alert)
        alerts.append(alert)

    if alerts:
        await db.commit()
    return alerts
