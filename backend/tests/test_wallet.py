import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_wallet_zero(client: AsyncClient, user_token):
    response = await client.get(
        "/api/wallet",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["balance"] == 0.0


@pytest.mark.asyncio
async def test_wallet_credited_on_approval(client: AsyncClient, admin_token, pending_submission):
    await client.patch(
        f"/api/admin/cards/submissions/{pending_submission}/review",
        json={"status": "approved", "admin_notes": "OK"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    response = await client.get(
        "/api/wallet",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.json()["balance"] > 0
