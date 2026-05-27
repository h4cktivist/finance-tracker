"""Кэшбэк: порог минимальной суммы покупки по правилу."""

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient


def _ok(resp, expected_status: int = 200) -> dict:
    assert resp.status_code == expected_status, (
        f"{resp.request.method} {resp.request.url} -> {resp.status_code}: {resp.text}"
    )
    return resp.json()


@pytest.mark.asyncio
async def test_cashback_skipped_below_min_purchase_amount(client: AsyncClient) -> None:
    email = "mincb@example.com"
    password = "secret12345"
    _ok(await client.post("/api/v1/auth/register", json={"email": email, "password": password}))
    login = _ok(
        await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    )
    headers = {"Authorization": f"Bearer {login['data']['access_token']}"}

    _ok(
        await client.post(
            "/api/v1/accounts",
            json={"name": "Main", "type": "cash", "initial_balance": "50000"},
            headers=headers,
        )
    )
    card_acc = _ok(
        await client.post(
            "/api/v1/accounts",
            json={"name": "CardAcc", "type": "credit", "initial_balance": "0"},
            headers=headers,
        )
    )["data"]
    cat = _ok(
        await client.post(
            "/api/v1/categories",
            json={"name": "Shop", "type": "expense"},
            headers=headers,
        )
    )["data"]
    card = _ok(
        await client.post(
            "/api/v1/cashback/cards",
            json={
                "account_id": card_acc["id"],
                "name": "Visa",
                "bank_name": "Bank",
                "last_digits": "4242",
            },
            headers=headers,
        )
    )["data"]
    today = date.today().isoformat()
    rule = _ok(
        await client.post(
            f"/api/v1/cashback/cards/{card['id']}/rules",
            json={
                "category_id": cat["id"],
                "cashback_percent": "10",
                "min_purchase_amount": "2000",
                "start_date": today,
            },
            headers=headers,
        )
    )["data"]
    assert rule.get("min_purchase_amount") is not None
    sum0 = _ok(await client.get("/api/v1/cashback/summary", headers=headers))["data"]
    assert Decimal(str(sum0["total_earned"])) == Decimal("0")

    _ok(
        await client.post(
            "/api/v1/transactions",
            json={
                "account_id": card_acc["id"],
                "category_id": cat["id"],
                "type": "expense",
                "amount": "1500",
                "transaction_date": today,
                "card_id": card["id"],
            },
            headers=headers,
        )
    )
    sum1 = _ok(await client.get("/api/v1/cashback/summary", headers=headers))["data"]
    assert Decimal(str(sum1["total_earned"])) == Decimal("0")

    _ok(
        await client.post(
            "/api/v1/transactions",
            json={
                "account_id": card_acc["id"],
                "category_id": cat["id"],
                "type": "expense",
                "amount": "2500",
                "transaction_date": today,
                "card_id": card["id"],
            },
            headers=headers,
        )
    )
    sum2 = _ok(await client.get("/api/v1/cashback/summary", headers=headers))["data"]
    expected = Decimal("2500") * Decimal("10") / Decimal("100")
    assert Decimal(str(sum2["total_earned"])) == expected

    recs = _ok(
        await client.get(
            "/api/v1/cashback/recommendations",
            params={"category_id": cat["id"]},
            headers=headers,
        )
    )["data"]
    assert len(recs) >= 1
    assert recs[0].get("min_purchase_amount") is not None
