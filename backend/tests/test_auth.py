import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!",
        "phone": "+2348012345678",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "dup@example.com",
        "password": "SecurePass123!",
        "phone": "+2348012345678",
    })
    response = await client.post("/api/auth/register", json={
        "email": "dup@example.com",
        "password": "SecurePass123!",
        "phone": "+2348098765432",
    })
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "login@example.com",
        "password": "SecurePass123!",
        "phone": "+2348012345678",
    })
    response = await client.post("/api/auth/login", json={
        "email": "login@example.com",
        "password": "SecurePass123!",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "wrong@example.com",
        "password": "SecurePass123!",
        "phone": "+2348012345678",
    })
    response = await client.post("/api/auth/login", json={
        "email": "wrong@example.com",
        "password": "WrongPass123!",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "me@example.com",
        "password": "SecurePass123!",
        "phone": "+2348012345678",
    })
    login_resp = await client.post("/api/auth/login", json={
        "email": "me@example.com",
        "password": "SecurePass123!",
    })
    token = login_resp.json()["access_token"]
    response = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401
