import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_reset_password_requires_token(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "resetuser@example.com", "password": "securepass123"},
    )
    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"email": "resetuser@example.com", "new_password": "newpass12345"},
    )
    assert resp.status_code == 422
    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"email": "resetuser@example.com", "reset_token": "garbage"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reset_password_request_does_not_reveal_existence(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/reset-password", json={"email": "nonexistent@example.com"}
    )
    assert resp.status_code == 200
    assert "exists" in resp.json()["message"]
