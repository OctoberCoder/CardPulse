import pytest


@pytest.mark.asyncio
async def test_mock_client_list_products():
    from app.services.reloadly import MockReloadlyClient
    client = MockReloadlyClient()
    products = await client.list_products()
    assert len(products) == 2
    assert products[0]["productName"] == "Amazon $100"


@pytest.mark.asyncio
async def test_mock_client_place_order():
    from app.services.reloadly import MockReloadlyClient
    client = MockReloadlyClient()
    result = await client.place_order(1, 1, "test@example.com")
    assert result["status"] == "SUCCESSFUL"


@pytest.mark.asyncio
async def test_mock_client_balance():
    from app.services.reloadly import MockReloadlyClient
    client = MockReloadlyClient()
    balance = await client.get_balance()
    assert balance["balance"] == 500.0


@pytest.mark.asyncio
async def test_get_reloadly_client_returns_mock():
    from app.services.reloadly import get_reloadly_client, MockReloadlyClient
    client = get_reloadly_client()
    assert isinstance(client, MockReloadlyClient)
