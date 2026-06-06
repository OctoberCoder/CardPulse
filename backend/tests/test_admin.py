import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_list_submissions(client: AsyncClient, admin_token, pending_submission):
    response = await client.get(
        "/api/admin/cards/submissions",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["status"] == "pending"


@pytest.mark.asyncio
async def test_admin_approve_submission(client: AsyncClient, admin_token, pending_submission):
    response = await client.patch(
        f"/api/admin/cards/submissions/{pending_submission}/review",
        json={"status": "approved", "admin_notes": "Code verified"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert response.json()["admin_notes"] == "Code verified"


@pytest.mark.asyncio
async def test_admin_reject_submission(client: AsyncClient, admin_token, pending_submission):
    response = await client.patch(
        f"/api/admin/cards/submissions/{pending_submission}/review",
        json={"status": "rejected", "admin_notes": "Invalid code"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_non_admin_cannot_review(client: AsyncClient, user_token, pending_submission):
    response = await client.patch(
        f"/api/admin/cards/submissions/{pending_submission}/review",
        json={"status": "approved", "admin_notes": ""},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403
