from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from app.config import get_settings
from app.routers import auth, cards

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title=settings.app_name, version="0.1.0", debug=settings.debug)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router)
app.include_router(cards.router)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}