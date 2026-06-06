import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_kyc(client: AsyncClient, user_token):
    response = await client.post(
        "/api/kyc/upload",
        files={"file": ("id.jpg", b"fake-image-data", "image/jpeg")},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_kyc_status(client: AsyncClient, user_token):
    response = await client.get("/api/kyc/status", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    assert "kyc_status" in response.json()
