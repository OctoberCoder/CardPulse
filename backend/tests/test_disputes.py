import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_open_dispute_no_order(client: AsyncClient, user_token):
    response = await client.post(
        "/api/disputes/orders/999/dispute?reason=broken",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_open_dispute_success(client: AsyncClient, user_token):
    order_resp = await client.post("/api/orders", json={
        "source": "reloadly", "listing_id": 1, "payment_method": "paystack",
    }, headers={"Authorization": f"Bearer {user_token}"})
    order_id = order_resp.json()["id"]

    response = await client.post(
        f"/api/disputes/orders/{order_id}/dispute?reason=Invalid+code",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["reason"] == "Invalid code"
    assert data["status"] == "open"
