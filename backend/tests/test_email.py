"""Tests for email service (MailgunClient, MockMailgunClient, EmailService)."""
import pytest
from app.services.email import (
    EmailService,
    MailgunClient,
    MockMailgunClient,
    get_email_service,
    format_amount,
)


class TestMockMailgunClient:
    async def test_send_stores_email(self):
        client = MockMailgunClient()
        service = EmailService(sender_email="test@example.com", client=client)

        result = await service.send("user@test.com", "Subject", "<p>Body</p>")

        assert result is True
        assert len(client.sent_emails) == 1
        assert client.sent_emails[0]["to"] == "user@test.com"
        assert client.sent_emails[0]["subject"] == "Subject"
        assert "<p>Body</p>" in client.sent_emails[0]["html"]

    async def test_multiple_sends(self):
        client = MockMailgunClient()
        service = EmailService(sender_email="test@example.com", client=client)

        await service.send("a@t.com", "S1", "<p>1</p>")
        await service.send("b@t.com", "S2", "<p>2</p>")

        assert len(client.sent_emails) == 2


class TestFormatAmount:
    def test_format_usd(self):
        assert format_amount(75.0) == "USD 75.00"
        assert format_amount(100.5) == "USD 100.50"
        assert format_amount(0) == "USD 0.00"

    def test_format_custom_currency(self):
        assert format_amount(50, "NGN") == "NGN 50.00"


class TestEmailService:
    def test_get_subject_known(self):
        service = EmailService("n@c.com", MockMailgunClient())
        assert "approved" in service.get_subject("submission_approved").lower()

    def test_get_subject_unknown(self):
        service = EmailService("n@c.com", MockMailgunClient())
        assert service.get_subject("nonexistent") == "CardPulse Notification"

    def test_render_template_escapes_html(self):
        service = EmailService("n@c.com", MockMailgunClient())
        html = service.render_template("submission_rejected", {
            "brand_name": "Test",
            "reason": "<script>alert('xss')</script>",
        })
        assert "&lt;script&gt;" in html
        assert "<script>" not in html

    def test_render_template_with_amount(self):
        service = EmailService("n@c.com", MockMailgunClient())
        html = service.render_template("submission_approved", {
            "brand_name": "Amazon",
            "amount": 75.0,
        })
        assert "USD 75.00" in html
        assert "Amazon" in html


class TestGetEmailService:
    def test_no_config_uses_mock(self, monkeypatch):
        monkeypatch.setattr("app.services.email.get_settings", lambda: type("S", (), {
            "mailgun_api_key": "",
            "mailgun_domain": "",
            "mailgun_sender_email": "n@c.com",
        })())
        service = get_email_service()
        assert isinstance(service.client, MockMailgunClient)

    def test_partial_config_uses_mock(self, monkeypatch):
        monkeypatch.setattr("app.services.email.get_settings", lambda: type("S", (), {
            "mailgun_api_key": "key-abc",
            "mailgun_domain": "",
            "mailgun_sender_email": "n@c.com",
        })())
        service = get_email_service()
        assert isinstance(service.client, MockMailgunClient)

    def test_full_config_uses_real_client(self, monkeypatch):
        monkeypatch.setattr("app.services.email.get_settings", lambda: type("S", (), {
            "mailgun_api_key": "key-abc",
            "mailgun_domain": "mg.example.com",
            "mailgun_sender_email": "noreply@mg.example.com",
        })())
        service = get_email_service()
        assert not isinstance(service.client, MockMailgunClient)
        assert service.client.domain == "mg.example.com"
        assert service.client.api_key == "key-abc"
