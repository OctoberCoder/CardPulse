"""Seed production database with initial data."""
import asyncio
from app.database import async_session
from app.models.card import CardBrand, Denomination
from app.models.reloadly import ReloadlyProduct
from app.models.user import User
from app.services.auth import hash_password


async def seed():
    async with async_session() as db:
        admin = User(email="admin@cardpulse.com", password_hash=hash_password("Admin123!"),
                     phone="+2348000000000", is_staff=True, tier="premium")
        user = User(email="user@cardpulse.com", password_hash=hash_password("User123!"),
                    phone="+2348012345678")
        db.add_all([admin, user])
        await db.commit()
        print("✅ Users: admin@cardpulse.com / Admin123!  |  user@cardpulse.com / User123!")

        for name in ["Amazon", "Apple", "Google Play", "Steam", "Netflix", "Spotify"]:
            slug = name.lower().replace(" ", "-")
            brand = CardBrand(name=name, slug=slug, active=True)
            db.add(brand)
            await db.commit()
            await db.refresh(brand)
            for val in [10, 25, 50, 100, 200]:
                db.add(Denomination(brand_id=brand.id, value=float(val), currency="USD"))
            await db.commit()
        print("✅ 6 brands with denominations")

        for rid, brand, denom, price in [
            (1, "Amazon", 100, 94.5), (2, "Amazon", 50, 47.25),
            (3, "Apple", 100, 93.0), (4, "Apple", 50, 46.5),
            (5, "Google Play", 50, 46.0), (6, "Google Play", 25, 23.0),
            (7, "Steam", 50, 47.0), (8, "Netflix", 25, 23.5),
        ]:
            db.add(ReloadlyProduct(reloadly_id=rid, brand=brand, denomination=denom,
                   sell_price=price, fee=0.5))
        await db.commit()
        print("✅ 8 Reloadly products")
        print("\nSeeding complete!")

asyncio.run(seed())
