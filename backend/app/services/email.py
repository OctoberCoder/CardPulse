"""Email service for sending transactional emails via Mailgun API."""
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "email_templates"

SUBJECTS = {
    "submission_approved": "Your Card Sale Has Been Approved - CardPulse",
    "submission_rejected": "Card Submission Update - CardPulse",
    "order_completed": "Your Order Is Complete - CardPulse",
    "payout_processed": "Your Payout Has Been Processed - CardPulse",
    "dispute_resolved": "Dispute Resolution Update - CardPulse",
}


def format_amount(value, currency="USD"):
    return f"{currency} {float(value):,.2f}"


class MailgunClient:
    """Real Mailgun API sender using httpx."""

    def __init__(self, api_key: str, domain: str):
        self.api_key = api_key
        self.domain = domain
        self.base_url = f"https://api.mailgun.net/v3/{domain}/messages"

    async def send(self, from_email: str, to: str, subject: str, html: str) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.base_url,
                auth=("api", self.api_key),
                data={
                    "from": from_email,
                    "to": to,
                    "subject": subject,
                    "html": html,
                },
            )
            resp.raise_for_status()
            return True


class MockMailgunClient:
    """Mock Mailgun client that logs instead of sending."""

    def __init__(self):
        self.sent_emails: list[dict] = []

    async def send(self, from_email: str, to: str, subject: str, html: str) -> bool:
        self.sent_emails.append({
            "from": from_email,
            "to": to,
            "subject": subject,
            "html": html,
        })
        logger.info("Mock email sent to %s: %s", to, subject)
        return True


class EmailService:
    """High-level email service: render templates + send via Mailgun."""

    def __init__(self, sender_email: str, client: MailgunClient | MockMailgunClient):
        self.sender_email = sender_email
        self.client = client
        self._env = self._build_jinja_env()

    def _build_jinja_env(self) -> Environment:
        env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        env.globals["format_amount"] = format_amount
        return env

    def render_template(self, template_name: str, context: dict) -> str:
        template = self._env.get_template(f"{template_name}.html")
        return template.render(**context)

    def get_subject(self, template_name: str) -> str:
        return SUBJECTS.get(template_name, "CardPulse Notification")

    async def send(self, to: str, subject: str, html: str) -> bool:
        return await self.client.send(self.sender_email, to, subject, html)

    async def send_template(self, template_name: str, context: dict, to: str) -> bool:
        html = self.render_template(template_name, context)
        subject = self.get_subject(template_name)
        return await self.send(to, subject, html)


def get_email_service(settings=None):
    """Factory: returns EmailService with real or mock client based on config."""
    settings = settings or get_settings()
    if settings.mailgun_api_key and settings.mailgun_domain:
        client = MailgunClient(
            api_key=settings.mailgun_api_key,
            domain=settings.mailgun_domain,
        )
        logger.info("Mailgun client initialized for domain: %s", settings.mailgun_domain)
    else:
        client = MockMailgunClient()
        logger.info("Mailgun not configured, using mock email client")
    return EmailService(sender_email=settings.mailgun_sender_email, client=client)
