"""Celery task for sending transactional emails asynchronously."""
import asyncio
import logging

import httpx

from app.celery_app import celery_app
from app.database import async_session
from app.models.notification import Notification
from app.services.email import get_email_service
from app.config import get_settings

logger = logging.getLogger(__name__)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    autoretry_for=(httpx.HTTPError,),
    max_retries=3,
    retry_backoff=60,
    retry_backoff_max=600,
    retry_jitter=True,
)
def send_email_task(notification_id: int, template_name: str, context: dict, to_email: str):
    """Render and send a transactional email, then mark notification as sent."""
    settings = get_settings()
    service = get_email_service(settings)

    html = service.render_template(template_name, context)
    subject = service.get_subject(template_name)

    logger.info(
        "Sending email: notification_id=%s template=%s to=%s subject=%s",
        notification_id, template_name, to_email, subject,
    )

    async def _send_and_mark():
        success = await service.send(to_email, subject, html)
        if not success:
            logger.warning(
                "Failed to send email: notification_id=%s template=%s to=%s",
                notification_id, template_name, to_email,
            )
            return False
        async with async_session() as db:
            notif = await db.get(Notification, notification_id)
            if notif:
                notif.email_sent = True
                await db.commit()
                logger.info("Marked notification %s as email_sent", notification_id)
        return True

    return run_async(_send_and_mark())
