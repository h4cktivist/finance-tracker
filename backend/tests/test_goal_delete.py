"""Финансовые цели: удаление."""

import pytest
from httpx import AsyncClient


def _ok(resp, expected_status: int = 200) -> dict:
    assert resp.status_code == expected_status, (
        f"{resp.request.method} {resp.request.url} -> {resp.status_code}: {resp.text}"
    )
    return resp.json()


async def _auth_headers(client: AsyncClient) -> dict:
    email = f"goal-del-{id(client)}@example.com"
    password = "secret12345"
    _ok(await client.post("/api/v1/auth/register", json={"email": email, "password": password}))
    login = _ok(
        await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    )
    return {"Authorization": f"Bearer {login['data']['access_token']}"}


@pytest.mark.asyncio
async def test_delete_goal_removes_it_from_list(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    kept = _ok(
        await client.post(
            "/api/v1/goals",
            json={"name": "Отпуск", "target_amount": "100000"},
            headers=headers,
        )
    )["data"]
    doomed = _ok(
        await client.post(
            "/api/v1/goals",
            json={"name": "Машина", "target_amount": "500000"},
            headers=headers,
        )
    )["data"]

    _ok(await client.delete(f"/api/v1/goals/{doomed['id']}", headers=headers))

    goals = _ok(await client.get("/api/v1/goals", headers=headers))["data"]
    assert [g["id"] for g in goals] == [kept["id"]]
    _ok(await client.get(f"/api/v1/goals/{doomed['id']}/progress", headers=headers), 404)


@pytest.mark.asyncio
async def test_delete_goal_twice_returns_404(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    goal = _ok(
        await client.post(
            "/api/v1/goals",
            json={"name": "Ноутбук", "target_amount": "150000"},
            headers=headers,
        )
    )["data"]
    _ok(await client.delete(f"/api/v1/goals/{goal['id']}", headers=headers))
    _ok(await client.delete(f"/api/v1/goals/{goal['id']}", headers=headers), 404)


@pytest.mark.asyncio
async def test_delete_goal_keeps_linked_account_and_its_transactions(
    client: AsyncClient,
) -> None:
    """Удаление цели не затрагивает привязанный счёт."""
    headers = await _auth_headers(client)
    account = _ok(
        await client.post(
            "/api/v1/accounts",
            json={"name": "Копилка", "type": "savings", "initial_balance": "5000"},
            headers=headers,
        )
    )["data"]
    goal = _ok(
        await client.post(
            "/api/v1/goals",
            json={
                "name": "На ремонт",
                "target_amount": "300000",
                "linked_account_id": account["id"],
            },
            headers=headers,
        )
    )["data"]

    _ok(await client.delete(f"/api/v1/goals/{goal['id']}", headers=headers))

    account_after = _ok(
        await client.get(f"/api/v1/accounts/{account['id']}", headers=headers)
    )["data"]
    assert account_after["id"] == account["id"]


@pytest.mark.asyncio
async def test_cannot_delete_another_users_goal(client: AsyncClient) -> None:
    owner = await _auth_headers(client)
    goal = _ok(
        await client.post(
            "/api/v1/goals",
            json={"name": "Личная цель", "target_amount": "10000"},
            headers=owner,
        )
    )["data"]

    email = f"goal-other-{id(client)}@example.com"
    password = "secret12345"
    _ok(await client.post("/api/v1/auth/register", json={"email": email, "password": password}))
    login = _ok(
        await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    )
    stranger = {"Authorization": f"Bearer {login['data']['access_token']}"}

    _ok(await client.delete(f"/api/v1/goals/{goal['id']}", headers=stranger), 404)
    goals = _ok(await client.get("/api/v1/goals", headers=owner))["data"]
    assert [g["id"] for g in goals] == [goal["id"]]
