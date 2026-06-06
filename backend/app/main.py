from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from app.config import get_settings
from app.routers import auth, cards, admin, wallet, pricing, products
from app.admin_setup import setup_admin

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title=settings.app_name, version="0.1.0", debug=settings.debug)
setup_admin(app)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router)
app.include_router(cards.router)
app.include_router(admin.router)
app.include_router(wallet.router)
app.include_router(pricing.router)
app.include_router(products.router)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}