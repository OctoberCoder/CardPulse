from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.reloadly import ReloadlyProduct
from app.config import get_settings

router = APIRouter(prefix="/api/products", tags=["products"])

RELOADLY_MARKUP = 0.05


@router.get("")
async def list_products(
    brand: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Merged product feed: Reloadly products + own inventory."""
    settings = get_settings()

    reloadly_result = await db.execute(
        select(ReloadlyProduct).where(ReloadlyProduct.active == True)
    )
    reloadly_products = reloadly_result.scalars().all()

    merged = []
    for rp in reloadly_products:
        price = round(rp.sell_price * (1 + RELOADLY_MARKUP), 2)
        merged.append({
            "id": f"reloadly-{rp.id}",
            "source": "reloadly",
            "brand": rp.brand,
            "denomination": rp.denomination,
            "price": price,
            "currency": rp.currency,
            "fee": rp.fee,
        })

    try:
        from app.models.card import OwnListing
        own_result = await db.execute(
            select(OwnListing).where(OwnListing.status == "available")
        )
        own_listings = own_result.scalars().all()
        for listing in own_listings:
            merged.append({
                "id": f"own-{listing.id}",
                "source": "own",
                "brand": listing.brand.name if hasattr(listing, 'brand') and listing.brand else "",
                "denomination": listing.denomination.value if hasattr(listing, 'denomination') and listing.denomination else 0,
                "price": listing.sell_price,
                "currency": "USD",
            })
    except (ImportError, AttributeError):
        pass

    if brand:
        merged = [p for p in merged if brand.lower() in p["brand"].lower()]
    if min_price is not None:
        merged = [p for p in merged if p["price"] >= min_price]
    if max_price is not None:
        merged = [p for p in merged if p["price"] <= max_price]

    return merged


@router.get("/reloadly")
async def list_reloadly_products(db: AsyncSession = Depends(get_db)):
    """Reloadly-only products (admin use / debugging)."""
    result = await db.execute(
        select(ReloadlyProduct).where(ReloadlyProduct.active == True)
    )
    products = result.scalars().all()
    return [{
        "id": p.id,
        "reloadly_id": p.reloadly_id,
        "brand": p.brand,
        "denomination": p.denomination,
        "price": p.sell_price,
        "currency": p.currency,
        "fee": p.fee,
    } for p in products]


@router.post("/reloadly/order")
async def place_reloadly_order(
    product_id: int,
    recipient_email: str,
    db: AsyncSession = Depends(get_db),
):
    """Place an order with Reloadly for a product."""
    from app.services.reloadly import get_reloadly_client
    client = get_reloadly_client()
    result = await client.place_order(product_id, 1, recipient_email)
    return {"transaction_id": result.get("transactionId"), "status": result.get("status")}
