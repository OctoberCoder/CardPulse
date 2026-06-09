import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.celery_tasks.email import send_email_task

logger = logging.getLogger(__name__)


async def create_notification(
    db: AsyncSession,
    user_id: int,
    type_: NotificationType,
    title: str,
    message: str,
    dedupe_key: str | None = None,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        type=type_,
        title=title,
        message=message,
        dedupe_key=dedupe_key,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return notif


async def notify_user(
    db: AsyncSession,
    user_id: int,
    notif_type: NotificationType,
    title: str,
    message: str,
    dedupe_key: str,
    email_template: str | None = None,
    email_context: dict | None = None,
) -> Notification | None:
    """Create an in-app notification and optionally enqueue an email.

    If a notification with the same dedupe_key already exists for this
    user, returns None (no-op). Email delivery is fire-and-forget via
    Celery — failures do not propagate to the caller.
    """
    if dedupe_key:
        existing = await db.execute(
            select(Notification).where(
                Notification.dedupe_key == dedupe_key,
                Notification.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none():
            logger.info("Duplicate notification skipped: dedupe_key=%s user=%s", dedupe_key, user_id)
            return None

    notif = await create_notification(db, user_id, notif_type, title, message, dedupe_key)

    if email_template and email_context:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user and user.email and "@" in user.email:
            try:
                send_email_task.delay(
                    notification_id=notif.id,
                    template_name=email_template,
                    context=email_context,
                    to_email=user.email,
                )
            except Exception as e:
                logger.error("Failed to enqueue email for notification %s: %s", notif.id, e)

    return notif


async def notify_submission_approved(db: AsyncSession, submission) -> Notification | None:
    return await notify_user(
        db, submission.user_id,
        NotificationType.SUBMISSION_APPROVED,
        "Card Sale Approved",
        f"Your gift card was approved! ${submission.final_amount:.2f} added to your wallet.",
        dedupe_key=f"submission:{submission.id}",
        email_template="submission_approved",
        email_context={
            "amount": submission.final_amount,
            "brand_name": submission.brand.name if hasattr(submission, 'brand') and submission.brand else "Gift Card",
        },
    )


async def notify_submission_rejected(db: AsyncSession, submission) -> Notification | None:
    reason = submission.admin_notes or "Does not meet our purchase criteria"
    return await notify_user(
        db, submission.user_id,
        NotificationType.SUBMISSION_REJECTED,
        "Card Sale Rejected",
        f"Your gift card submission was not approved: {reason}",
        dedupe_key=f"submission:{submission.id}",
        email_template="submission_rejected",
        email_context={
            "brand_name": submission.brand.name if hasattr(submission, 'brand') and submission.brand else "Gift Card",
            "reason": reason,
        },
    )


async def notify_order_completed(db: AsyncSession, order) -> Notification | None:
    return await notify_user(
        db, order.user_id,
        NotificationType.ORDER_COMPLETED,
        "Order Complete",
        f"Order #{order.id} has been completed. Your card code is ready.",
        dedupe_key=f"order:{order.id}",
        email_template="order_completed",
        email_context={
            "order_id": order.id,
            "product_name": order.product_name if hasattr(order, 'product_name') else "Gift Card",
        },
    )


async def notify_payout_processed(db: AsyncSession, user_id: int, amount: float, method: str, payout_id: int) -> Notification | None:
    return await notify_user(
        db, user_id,
        NotificationType.PAYOUT_PROCESSED,
        "Payout Processed",
        f"Your payout of ${amount:.2f} has been processed via {method}.",
        dedupe_key=f"payout:{payout_id}",
        email_template="payout_processed",
        email_context={
            "amount": amount,
            "method": method,
        },
    )


async def notify_dispute_resolved(db: AsyncSession, dispute) -> Notification | None:
    return await notify_user(
        db, dispute.user_id,
        NotificationType.DISPUTE_RESOLVED,
        "Dispute Resolved",
        f"Dispute #{dispute.id} has been resolved. Outcome: {dispute.status}",
        dedupe_key=f"dispute:{dispute.id}",
        email_template="dispute_resolved",
        email_context={
            "dispute_id": dispute.id,
            "outcome": dispute.status.value if hasattr(dispute.status, 'value') else str(dispute.status),
        },
    )
