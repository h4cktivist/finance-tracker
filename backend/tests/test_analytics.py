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


@pytest.mark.asyncio
async def test_exclude_investments_from_statistics(client: AsyncClient):
    headers = await _auth_headers(client, "analytics-inv@example.com")
    account_id = (
        await client.post(
            "/api/v1/accounts",
            json={"name": "Wallet", "type": "cash", "initial_balance": "10000"},
            headers=headers,
        )
    ).json()["data"]["id"]
    food_id = (
        await client.post(
            "/api/v1/categories", json={"name": "Еда", "type": "expense"}, headers=headers
        )
    ).json()["data"]["id"]
    invest_id = (
        await client.post(
            "/api/v1/categories",
            json={"name": "Инвестиции", "type": "expense"},
            headers=headers,
        )
    ).json()["data"]["id"]
    today = date.today().isoformat()
    for category_id, amount in ((food_id, "100"), (invest_id, "500")):
        resp = await client.post(
            "/api/v1/transactions",
            json={
                "account_id": account_id,
                "category_id": category_id,
                "type": "expense",
                "amount": amount,
                "transaction_date": today,
            },
            headers=headers,
        )
        assert resp.status_code == 200

    all_stats = (
        await client.get("/api/v1/analytics/statistics", headers=headers)
    ).json()["data"]
    filtered_stats = (
        await client.get(
            "/api/v1/analytics/statistics",
            headers=headers,
            params={"exclude_investments": True},
        )
    ).json()["data"]

    assert Decimal(str(all_stats["average_daily_spending"])) == Decimal("600")
    assert Decimal(str(filtered_stats["average_daily_spending"])) == Decimal("100")
    expense_names = [c["category_name"] for c in filtered_stats["top_expense_categories"]]
    assert "Инвестиции" not in expense_names
    assert "Еда" in expense_names
