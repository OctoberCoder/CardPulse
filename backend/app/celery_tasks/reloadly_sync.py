"""Celery task to sync Reloadly products into the database."""
from app.celery_app import celery_app
from app.services.reloadly import get_reloadly_client
from app.database import async_session
from app.models.reloadly import ReloadlyProduct
from sqlalchemy import select
from datetime import datetime, timezone
import asyncio


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task
def sync_reloadly_products():
    """Fetch all products from Reloadly API and upsert into database."""
    client = get_reloadly_client()
    page = 1
    total = 0

    async def _sync():
        nonlocal total
        async with async_session() as db:
            while True:
                products = await client.list_products(page=page)
                if not products:
                    break
                for p in products:
                    denoms = p.get("fixedRecipientDenominations", [100])
                    denom = float(denoms[0]) if denoms else 100.0
                    result = await db.execute(
                        select(ReloadlyProduct).where(ReloadlyProduct.reloadly_id == p["id"])
                    )
                    existing = result.scalar_one_or_none()
                    if existing:
                        existing.sell_price = denom
                        existing.brand = p.get("productName", existing.brand)
                        existing.last_synced = datetime.now(timezone.utc)
                    else:
                        db.add(ReloadlyProduct(
                            reloadly_id=p["id"],
                            brand=p.get("productName", "Unknown"),
                            denomination=denom,
                            currency=p.get("targetCurrency", "USD"),
                            sell_price=denom,
                            fee=p.get("senderFee", 0.0),
                        ))
                    total += 1
                page += 1
            await db.commit()
        return total

    return run_async(_sync())
