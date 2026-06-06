import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_rate_rule(client: AsyncClient, admin_token, db_session):
    from app.models.card import CardBrand, Denomination
    brand = CardBrand(name="Amazon", slug="amazon")
    db_session.add(brand)
    await db_session.commit()
    denom = Denomination(brand_id=brand.id, value=100.0)
    db_session.add(denom)
    await db_session.commit()

    response = await client.post("/api/admin/rates", json={
        "brand_id": brand.id,
        "denomination_id": denom.id,
        "base_buy_rate": 0.75,
        "adjustments": [
            {"trigger_type": "stock_low", "operator": "add", "value": 10, "adjustment_pct": 0.02},
        ],
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["base_buy_rate"] == 0.75
    assert len(data["adjustments"]) == 1


@pytest.mark.asyncio
async def test_get_effective_rates(client: AsyncClient, admin_token, db_session):
    from app.models.card import CardBrand, Denomination
    from app.models.pricing import RateRule
    brand = CardBrand(name="Apple", slug="apple")
    db_session.add(brand)
    await db_session.commit()
    denom = Denomination(brand_id=brand.id, value=50.0)
    db_session.add(denom)
    await db_session.commit()
    rule = RateRule(brand_id=brand.id, denomination_id=denom.id, base_buy_rate=0.70, sell_markup_pct=0.15)
    db_session.add(rule)
    await db_session.commit()

    response = await client.get("/api/admin/rates/effective",
                                headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_non_admin_cannot_create_rate(client: AsyncClient, user_token):
    response = await client.post("/api/admin/rates", json={
        "brand_id": 1, "denomination_id": 1, "base_buy_rate": 0.75,
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403
