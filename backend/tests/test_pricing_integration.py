import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_quote_uses_pricing_engine(client: AsyncClient, user_token, db_session):
    from app.models.card import CardBrand, Denomination
    from app.models.pricing import RateRule
    brand = CardBrand(name="Amazon", slug="amazon")
    db_session.add(brand)
    await db_session.commit()
    denom = Denomination(brand_id=brand.id, value=100.0)
    db_session.add(denom)
    await db_session.commit()
    rule = RateRule(brand_id=brand.id, denomination_id=denom.id, base_buy_rate=0.80)
    db_session.add(rule)
    await db_session.commit()

    response = await client.post("/api/cards/quote", json={
        "brand_id": brand.id, "denomination_id": denom.id, "card_code": "TEST",
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    assert response.json()["buy_rate"] == 0.80
    assert response.json()["quoted_amount"] == 80.0


@pytest.mark.asyncio
async def test_quote_falls_back_to_default(client: AsyncClient, user_token, db_session):
    from app.models.card import CardBrand, Denomination
    brand = CardBrand(name="Amazon", slug="amazon")
    db_session.add(brand)
    await db_session.commit()
    denom = Denomination(brand_id=brand.id, value=100.0)
    db_session.add(denom)
    await db_session.commit()

    response = await client.post("/api/cards/quote", json={
        "brand_id": brand.id, "denomination_id": denom.id, "card_code": "TEST",
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    assert response.json()["buy_rate"] == 0.75
    assert response.json()["quoted_amount"] == 75.0
