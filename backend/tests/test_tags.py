import pytest
from httpx import AsyncClient


async def _auth_headers(client: AsyncClient) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register", json={"email": "taguser@example.com", "password": "securepass123"}
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": "taguser@example.com", "password": "securepass123"}
    )
    token = login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_duplicate_tag_name_rejected(client: AsyncClient):
    headers = await _auth_headers(client)
    first = await client.post("/api/v1/tags", json={"name": "vacation"}, headers=headers)
    assert first.status_code == 200
    second = await client.post("/api/v1/tags", json={"name": "vacation"}, headers=headers)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "CONFLICT"
