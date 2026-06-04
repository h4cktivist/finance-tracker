from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient


async def _auth_headers(client: AsyncClient, email: str) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "securepass123"}
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "securepass123"}
    )
    token = login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _month_start(year: int, month: int) -> str:
    return date(year, month, 1).isoformat()


@pytest.mark.asyncio
async def test_budget_recommendations_suggest_create(client: AsyncClient):
    headers = await _auth_headers(client, "budget-rec-create@example.com")
    account_id = (
        await client.post(
            "/api/v1/accounts",
            json={"name": "Wallet", "type": "cash", "initial_balance": "0"},
            headers=headers,
        )
    ).json()["data"]["id"]
    food_id = (
        await client.post(
            "/api/v1/categories", json={"name": "Еда", "type": "expense"}, headers=headers
        )
    ).json()["data"]["id"]

    today = date.today()
    for offset in (2, 1, 0):
        m = today.month - offset
        y = today.year
        while m < 1:
            m += 12
            y -= 1
        for _ in range(3):
            await client.post(
                "/api/v1/transactions",
                json={
                    "account_id": account_id,
                    "category_id": food_id,
                    "type": "expense",
                    "amount": "2000",
                    "transaction_date": _month_start(y, m),
                },
                headers=headers,
            )

    resp = await client.get("/api/v1/budgets/recommendations", headers=headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    create_items = [i for i in items if i["recommendation_type"] == "create"]
    assert any(i["category_name"] == "Еда" for i in create_items)
    food = next(i for i in create_items if i["category_name"] == "Еда")
    assert Decimal(food["suggested_amount_limit"]) >= Decimal("6000")


@pytest.mark.asyncio
async def test_budget_recommendations_suggest_increase(client: AsyncClient):
    headers = await _auth_headers(client, "budget-rec-inc@example.com")
    account_id = (
        await client.post(
            "/api/v1/accounts",
            json={"name": "Wallet", "type": "cash", "initial_balance": "0"},
            headers=headers,
        )
    ).json()["data"]["id"]
    cat_id = (
        await client.post(
            "/api/v1/categories", json={"name": "Такси", "type": "expense"}, headers=headers
        )
    ).json()["data"]["id"]

    today = date.today()
    for offset in (2, 1, 0):
        m = today.month - offset
        y = today.year
        while m < 1:
            m += 12
            y -= 1
        await client.post(
            "/api/v1/transactions",
            json={
                "account_id": account_id,
                "category_id": cat_id,
                "type": "expense",
                "amount": "5000",
                "transaction_date": _month_start(y, m),
            },
            headers=headers,
        )
        await client.post(
            "/api/v1/transactions",
            json={
                "account_id": account_id,
                "category_id": cat_id,
                "type": "expense",
                "amount": "5000",
                "transaction_date": _month_start(y, m),
            },
            headers=headers,
        )

    await client.post(
        "/api/v1/budgets",
        json={
            "category_id": cat_id,
            "amount_limit": "8000",
            "period_type": "monthly",
            "start_date": today.replace(day=1).isoformat(),
        },
        headers=headers,
    )

    resp = await client.get("/api/v1/budgets/recommendations", headers=headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    inc = [i for i in items if i["recommendation_type"] == "increase" and i["category_name"] == "Такси"]
    assert len(inc) == 1
    assert Decimal(inc[0]["suggested_amount_limit"]) > Decimal("8000")
