import pytest
from httpx import AsyncClient
import hashlib


@pytest.mark.asyncio
async def test_create_order(client: AsyncClient, user_token):
    response = await client.post("/api/orders", json={
        "source": "reloadly",
        "listing_id": 1,
        "payment_method": "paystack",
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert "payment_url" in data


@pytest.mark.asyncio
async def test_create_order_idempotent(client: AsyncClient, user_token):
    key = "test-idemp-key-123"
    resp1 = await client.post("/api/orders", json={
        "source": "reloadly", "listing_id": 1, "payment_method": "paystack",
        "idempotency_key": key,
    }, headers={"Authorization": f"Bearer {user_token}"})
    resp2 = await client.post("/api/orders", json={
        "source": "reloadly", "listing_id": 1, "payment_method": "paystack",
        "idempotency_key": key,
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.json()["id"] == resp2.json()["id"]


@pytest.mark.asyncio
async def test_list_orders(client: AsyncClient, user_token):
    await client.post("/api/orders", json={
        "source": "reloadly", "listing_id": 1, "payment_method": "flutterwave",
    }, headers={"Authorization": f"Bearer {user_token}"})
    response = await client.get("/api/orders", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_paystack_webhook(client: AsyncClient, user_token):
    order_resp = await client.post("/api/orders", json={
        "source": "reloadly", "listing_id": 1, "payment_method": "paystack",
    }, headers={"Authorization": f"Bearer {user_token}"})
    ref = order_resp.json()["payment_reference"]

    body = f'{{"event":"charge.success","data":{{"reference":"{ref}"}}}}'.encode()
    sig = hashlib.sha256(body).hexdigest()
    response = await client.post(
        "/api/webhooks/paystack",
        content=body,
        headers={"x-paystack-signature": sig},
    )
    assert response.status_code == 200

    # Verify order was completed
    get_resp = await client.get(f"/api/orders/{order_resp.json()['id']}",
                                 headers={"Authorization": f"Bearer {user_token}"})
    assert get_resp.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_webhook_invalid_signature(client: AsyncClient):
    response = await client.post(
        "/api/webhooks/paystack",
        content=b'{"event":"charge.success"}',
        headers={"x-paystack-signature": "invalid"},
    )
    assert response.status_code == 401
