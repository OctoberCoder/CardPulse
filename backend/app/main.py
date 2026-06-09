import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from app.config import get_settings
from app.routers import auth, cards, admin, wallet, pricing, products, orders, webhooks, notifications, kyc, disputes
from app.admin_setup import setup_admin
from app.services.email import get_email_service

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.mailgun_api_key and not settings.mailgun_domain:
        logger.warning("MAILGUN_API_KEY set but MAILGUN_DOMAIN is empty — falling back to mock email")
    elif settings.mailgun_domain and not settings.mailgun_api_key:
        logger.warning("MAILGUN_DOMAIN set but MAILGUN_API_KEY is empty — falling back to mock email")
    elif settings.mailgun_api_key and settings.mailgun_domain:
        if settings.mailgun_domain not in settings.mailgun_sender_email:
            logger.warning(
                "MAILGUN_SENDER_EMAIL (%s) does not contain MAILGUN_DOMAIN (%s) — delivery may fail",
                settings.mailgun_sender_email, settings.mailgun_domain,
            )
        logger.info("Mailgun configured for domain: %s", settings.mailgun_domain)

    email_service = get_email_service(settings)
    app.state.email_service = email_service
    yield
    app.state.email_service = None


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.cardpulse.publicvm.com",
        "https://octobercoder.github.io",
        "http://localhost:8000",
        "http://localhost:5000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_admin(app)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router)
app.include_router(cards.router)
app.include_router(admin.router)
app.include_router(wallet.router)
app.include_router(pricing.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(webhooks.router)
app.include_router(notifications.router)
app.include_router(kyc.router)
app.include_router(disputes.router)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}