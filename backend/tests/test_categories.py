import pytest
from httpx import AsyncClient


async def _auth_headers(client: AsyncClient, suffix: str = "") -> dict[str, str]:
    email = f"catuser{suffix}@example.com"
    await client.post("/api/v1/auth/register", json={"email": email, "password": "securepass123"})
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "securepass123"}
    )
    token = login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_nested_category_tree(client: AsyncClient):
    headers = await _auth_headers(client)
    parent_resp = await client.post(
        "/api/v1/categories", json={"name": "Food", "type": "expense"}, headers=headers
    )
    assert parent_resp.status_code == 200
    parent_id = parent_resp.json()["data"]["id"]
    child_resp = await client.post(
        "/api/v1/categories",
        json={"name": "Restaurants", "type": "expense", "parent_category_id": parent_id},
        headers=headers,
    )
    assert child_resp.status_code == 200
    tree_resp = await client.get("/api/v1/categories/tree", headers=headers)
    assert tree_resp.status_code == 200
    roots = tree_resp.json()["data"]
    assert len(roots) == 1
    assert roots[0]["name"] == "Food"
    assert len(roots[0]["children"]) == 1
    assert roots[0]["children"][0]["name"] == "Restaurants"


@pytest.mark.asyncio
async def test_category_type_mismatch_rejected(client: AsyncClient):
    headers = await _auth_headers(client, suffix="-mismatch")
    parent_resp = await client.post(
        "/api/v1/categories", json={"name": "Salary", "type": "income"}, headers=headers
    )
    parent_id = parent_resp.json()["data"]["id"]
    bad_child = await client.post(
        "/api/v1/categories",
        json={"name": "Pizza", "type": "expense", "parent_category_id": parent_id},
        headers=headers,
    )
    assert bad_child.status_code == 422
