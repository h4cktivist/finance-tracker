import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    register_resp = await client.post(
        "/api/v1/auth/register", json={"email": "test@example.com", "password": "securepass123"}
    )
    assert register_resp.status_code == 200
    body = register_resp.json()
    assert body["success"] is True
    assert body["data"]["email"] == "test@example.com"
    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "test@example.com", "password": "securepass123"}
    )
    assert login_resp.status_code == 200
    login_body = login_resp.json()
    assert login_body["success"] is True
    assert "access_token" in login_body["data"]
    assert "refresh_token" in login_body["data"]


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "ok"
