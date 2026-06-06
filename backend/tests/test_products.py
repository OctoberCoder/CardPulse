import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_products_empty(client: AsyncClient):
    response = await client.get("/api/products")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_products_with_reloadly(client: AsyncClient, db_session):
    from app.models.reloadly import ReloadlyProduct
    rp = ReloadlyProduct(reloadly_id=1, brand="Amazon", denomination=100.0, sell_price=95.0)
    db_session.add(rp)
    await db_session.commit()

    response = await client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    sources = [p["source"] for p in data]
    assert "reloadly" in sources


@pytest.mark.asyncio
async def test_list_products_filter_by_brand(client: AsyncClient, db_session):
    from app.models.reloadly import ReloadlyProduct
    db_session.add(ReloadlyProduct(reloadly_id=1, brand="Amazon", denomination=100.0, sell_price=95.0))
    db_session.add(ReloadlyProduct(reloadly_id=2, brand="Apple", denomination=50.0, sell_price=47.0))
    await db_session.commit()

    response = await client.get("/api/products?brand=amazon")
    data = response.json()
    assert len(data) == 1
    assert "amazon" in data[0]["brand"].lower()


@pytest.mark.asyncio
async def test_list_reloadly_products_endpoint(client: AsyncClient, db_session):
    from app.models.reloadly import ReloadlyProduct
    db_session.add(ReloadlyProduct(reloadly_id=1, brand="Amazon", denomination=100.0, sell_price=95.0))
    await db_session.commit()

    response = await client.get("/api/products/reloadly")
    assert response.status_code == 200
    assert len(response.json()) == 1
