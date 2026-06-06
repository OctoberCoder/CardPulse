import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.card import CardBrand


@pytest.mark.asyncio
async def test_list_brands_empty(client: AsyncClient):
    response = await client.get("/api/brands")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_brand(client: AsyncClient, admin_token):
    brand_data = {"name": "Amazon", "slug": "amazon", "description": "Amazon gift cards"}
    response = await client.post("/api/admin/brands", json=brand_data,
                                 headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Amazon"
    assert data["slug"] == "amazon"


@pytest.mark.asyncio
async def test_list_brands_with_data(client: AsyncClient, admin_token):
    await client.post("/api/admin/brands", json={"name": "Amazon", "slug": "amazon"},
                      headers={"Authorization": f"Bearer {admin_token}"})
    response = await client.get("/api/brands")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_quote_card(client: AsyncClient, admin_token, db_session):
    await client.post("/api/admin/brands", json={"name": "Amazon", "slug": "amazon"},
                      headers={"Authorization": f"Bearer {admin_token}"})
    from app.models.card import Denomination
    result = await db_session.execute(select(CardBrand).where(CardBrand.slug == "amazon"))
    brand = result.scalar_one()
    denom = Denomination(brand_id=brand.id, value=100.0)
    db_session.add(denom)
    await db_session.commit()
    await db_session.refresh(denom)
    denom_id = denom.id

    from app.services.auth import create_access_token
    user_token = create_access_token(1)
    response = await client.post("/api/cards/quote", json={
        "brand_id": 1, "denomination_id": denom_id, "card_code": "TEST123",
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["quoted_amount"] == 75.0
    assert data["buy_rate"] == 0.75


@pytest.mark.asyncio
async def test_submit_card(client: AsyncClient, admin_token, db_session):
    await client.post("/api/admin/brands", json={"name": "Amazon", "slug": "amazon"},
                      headers={"Authorization": f"Bearer {admin_token}"})
    from app.models.card import Denomination
    result = await db_session.execute(select(CardBrand).where(CardBrand.slug == "amazon"))
    brand = result.scalar_one()
    denom = Denomination(brand_id=brand.id, value=50.0)
    db_session.add(denom)
    await db_session.commit()
    await db_session.refresh(denom)
    denom_id = denom.id

    from app.services.auth import create_access_token
    user_token = create_access_token(1)
    response = await client.post("/api/cards/submit", json={
        "brand_id": 1, "denomination_id": denom_id,
        "card_code": "CODE123", "quoted_amount": 37.5,
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 201
    assert response.json()["status"] == "pending"
