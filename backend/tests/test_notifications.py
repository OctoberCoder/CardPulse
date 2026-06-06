import pytest
from app.services.notifications import create_notification, notify_submission_approved
from app.models.notification import NotificationType


@pytest.mark.asyncio
async def test_create_notification(db_session):
    notif = await create_notification(
        db_session, user_id=1, type_=NotificationType.SUBMISSION_APPROVED,
        title="Test", message="Hello",
    )
    assert notif.title == "Test"
    assert notif.read is False


@pytest.mark.asyncio
async def test_notify_approved(db_session):
    await notify_submission_approved(db_session, user_id=1, amount=75.0)
    from sqlalchemy import select
    from app.models.notification import Notification
    result = await db_session.execute(select(Notification))
    notifs = result.scalars().all()
    assert len(notifs) == 1
    assert "$75" in notifs[0].message
