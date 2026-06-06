from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType


async def create_notification(
    db: AsyncSession,
    user_id: int,
    type_: NotificationType,
    title: str,
    message: str,
) -> Notification:
    notif = Notification(
        user_id=user_id, type=type_, title=title, message=message,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return notif


async def notify_submission_approved(db: AsyncSession, user_id: int, amount: float):
    await create_notification(
        db, user_id, NotificationType.SUBMISSION_APPROVED,
        "Card Sale Approved",
        f"Your gift card was approved! ${amount:.2f} added to your wallet.",
    )


async def notify_submission_rejected(db: AsyncSession, user_id: int, reason: str):
    await create_notification(
        db, user_id, NotificationType.SUBMISSION_REJECTED,
        "Card Sale Rejected",
        f"Your gift card submission was rejected: {reason}",
    )
