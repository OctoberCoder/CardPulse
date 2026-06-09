"""Tests for notification service (notify_user, dedupe, email enqueue)."""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models import Base
from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.services.notifications import notify_user, notify_submission_approved
from app.services.auth import hash_password


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        user = User(
            email="user@test.com",
            password_hash=hash_password("testpass"),
            phone="+1234567890",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        yield session
    await engine.dispose()


class TestNotifyUser:
    @patch("app.services.notifications.send_email_task.delay")
    async def test_creates_notification_and_enqueues_email(self, mock_delay, db_session):
        result = await notify_user(
            db_session, 1, NotificationType.SUBMISSION_APPROVED,
            "Test Title", "Test message",
            dedupe_key="test:1",
            email_template="submission_approved",
            email_context={"amount": 75.0, "brand_name": "Amazon"},
        )

        assert result is not None
        assert result.title == "Test Title"
        assert result.message == "Test message"
        assert result.dedupe_key == "test:1"
        assert result.email_sent is False

        mock_delay.assert_called_once_with(
            notification_id=result.id,
            template_name="submission_approved",
            context={"amount": 75.0, "brand_name": "Amazon"},
            to_email="user@test.com",
        )

    @patch("app.services.notifications.send_email_task.delay")
    async def test_dedupe_prevents_duplicates(self, mock_delay, db_session):
        first = await notify_user(
            db_session, 1, NotificationType.SUBMISSION_APPROVED,
            "First", "First msg",
            dedupe_key="submission:42",
            email_template="submission_approved",
            email_context={"amount": 10.0, "brand_name": "Test"},
        )
        second = await notify_user(
            db_session, 1, NotificationType.SUBMISSION_APPROVED,
            "Second", "Second msg",
            dedupe_key="submission:42",
            email_template="submission_approved",
            email_context={"amount": 10.0, "brand_name": "Test"},
        )

        assert first is not None
        assert second is None
        assert mock_delay.call_count == 1

    @patch("app.services.notifications.send_email_task.delay")
    async def test_same_key_different_users_creates_separate(self, mock_delay, db_session):
        user2 = User(
            email="user2@test.com",
            password_hash=hash_password("testpass"),
            phone="+9876543210",
        )
        db_session.add(user2)
        await db_session.commit()
        await db_session.refresh(user2)

        first = await notify_user(
            db_session, 1, NotificationType.SUBMISSION_APPROVED,
            "For user 1", "Msg",
            dedupe_key="submission:1",
            email_template="submission_approved",
            email_context={"amount": 10.0, "brand_name": "Test"},
        )
        second = await notify_user(
            db_session, 2, NotificationType.SUBMISSION_APPROVED,
            "For user 2", "Msg",
            dedupe_key="submission:1",
            email_template="submission_approved",
            email_context={"amount": 10.0, "brand_name": "Test"},
        )

        assert first is not None
        assert second is not None
        assert first.user_id != second.user_id
        assert mock_delay.call_count == 2

    @patch("app.services.notifications.send_email_task.delay")
    async def test_no_email_when_user_has_no_email(self, mock_delay, db_session):
        user_no_email = User(
            email="",
            password_hash=hash_password("testpass"),
            phone="+0000000000",
        )
        db_session.add(user_no_email)
        await db_session.commit()
        await db_session.refresh(user_no_email)

        result = await notify_user(
            db_session, user_no_email.id, NotificationType.SUBMISSION_APPROVED,
            "Title", "Msg",
            dedupe_key="submission:99",
            email_template="submission_approved",
            email_context={"amount": 10.0, "brand_name": "Test"},
        )

        assert result is not None
        mock_delay.assert_not_called()

    @patch("app.services.notifications.send_email_task.delay")
    async def test_repeated_admin_action_is_noop(self, mock_delay, db_session):
        first = await notify_user(
            db_session, 1, NotificationType.SUBMISSION_REJECTED,
            "Rejected", "Reason",
            dedupe_key="submission:5",
            email_template="submission_rejected",
            email_context={"brand_name": "Test", "reason": "Duplicate"},
        )
        second = await notify_user(
            db_session, 1, NotificationType.SUBMISSION_REJECTED,
            "Rejected again", "Another reason",
            dedupe_key="submission:5",
            email_template="submission_rejected",
            email_context={"brand_name": "Test", "reason": "Duplicate"},
        )

        assert first is not None
        assert second is None
        assert mock_delay.call_count == 1

    async def test_notify_submission_approved_convenience(self, db_session):
        submission = MagicMock()
        submission.user_id = 1
        submission.id = 100
        submission.final_amount = 50.0
        submission.brand = MagicMock()
        submission.brand.name = "Steam"

        with patch("app.services.notifications.send_email_task.delay") as mock_delay:
            result = await notify_submission_approved(db_session, submission)

        assert result is not None
        assert result.dedupe_key == "submission:100:approved"
        mock_delay.assert_called_once()
