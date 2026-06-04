from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "CardPulse"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cardpulse"
    database_url_sync: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/cardpulse"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    encryption_key: str = "change-me-in-production-32bytes!"
    rate_limit_auth: str = "5/minute"
    rate_limit_general: str = "30/minute"
    rate_limit_browse: str = "100/minute"
    sentry_dsn: str = ""
    logtail_token: str = ""
    reloadly_client_id: str = ""
    reloadly_client_secret: str = ""
    reloadly_environment: str = "sandbox"
    paystack_secret_key: str = ""
    flutterwave_secret_key: str = ""
    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()