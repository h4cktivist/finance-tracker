"""Кэшбэк: редактирование правила и пересчёт начислений."""

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
async def test_update_rule_recalculates_existing_transactions(client: AsyncClient) -> None:
    email = "ruleupd@example.com"
    password = "secret12345"
    _ok(await client.post("/api/v1/auth/register", json={"email": email, "password": password}))
    login = _ok(
        await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    )
    headers = {"Authorization": f"Bearer {login['data']['access_token']}"}

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
            json={"name": "Food", "type": "expense"},
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
                "last_digits": "1111",
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
                "cashback_percent": "5",
                "start_date": today,
            },
            headers=headers,
        )
    )["data"]

    _ok(
        await client.post(
            "/api/v1/transactions",
            json={
                "account_id": card_acc["id"],
                "category_id": cat["id"],
                "type": "expense",
                "amount": "1000",
                "transaction_date": today,
                "card_id": card["id"],
            },
            headers=headers,
        )
    )
    sum_before = _ok(await client.get("/api/v1/cashback/summary", headers=headers))["data"]
    assert Decimal(str(sum_before["total_earned"])) == Decimal("50")

    updated = _ok(
        await client.patch(
            f"/api/v1/cashback/cards/{card['id']}/rules/{rule['id']}",
            json={"cashback_percent": "10", "recalculate_existing": True},
            headers=headers,
        )
    )["data"]
    assert Decimal(str(updated["rule"]["cashback_percent"])) == Decimal("10")
    assert updated["recalculated_transactions"] == 1

    sum_after = _ok(await client.get("/api/v1/cashback/summary", headers=headers))["data"]
    assert Decimal(str(sum_after["total_earned"])) == Decimal("100")


@pytest.mark.asyncio
async def test_update_rule_without_recalculate_keeps_accruals(client: AsyncClient) -> None:
    email = "ruleupd2@example.com"
    password = "secret12345"
    _ok(await client.post("/api/v1/auth/register", json={"email": email, "password": password}))
    login = _ok(
        await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    )
    headers = {"Authorization": f"Bearer {login['data']['access_token']}"}

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
            json={"name": "Taxi", "type": "expense"},
            headers=headers,
        )
    )["data"]
    card = _ok(
        await client.post(
            "/api/v1/cashback/cards",
            json={"account_id": card_acc["id"], "name": "MC"},
            headers=headers,
        )
    )["data"]
    today = date.today().isoformat()
    rule = _ok(
        await client.post(
            f"/api/v1/cashback/cards/{card['id']}/rules",
            json={
                "category_id": cat["id"],
                "cashback_percent": "5",
                "start_date": today,
            },
            headers=headers,
        )
    )["data"]

    _ok(
        await client.post(
            "/api/v1/transactions",
            json={
                "account_id": card_acc["id"],
                "category_id": cat["id"],
                "type": "expense",
                "amount": "2000",
                "transaction_date": today,
                "card_id": card["id"],
            },
            headers=headers,
        )
    )

    _ok(
        await client.patch(
            f"/api/v1/cashback/cards/{card['id']}/rules/{rule['id']}",
            json={"cashback_percent": "20", "recalculate_existing": False},
            headers=headers,
        )
    )
    sum_after = _ok(await client.get("/api/v1/cashback/summary", headers=headers))["data"]
    assert Decimal(str(sum_after["total_earned"])) == Decimal("100")


@pytest.mark.asyncio
async def test_recalculate_clears_cashback_below_new_min_purchase(client: AsyncClient) -> None:
    """Повышение min_purchase_amount + пересчёт обнуляет кэшбэк у мелких покупок."""
    email = "minrecalc@example.com"
    password = "secret12345"
    _ok(await client.post("/api/v1/auth/register", json={"email": email, "password": password}))
    login = _ok(
        await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    )
    headers = {"Authorization": f"Bearer {login['data']['access_token']}"}

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
            json={"account_id": card_acc["id"], "name": "Visa"},
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
                "start_date": today,
            },
            headers=headers,
        )
    )["data"]

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
    sum_before = _ok(await client.get("/api/v1/cashback/summary", headers=headers))["data"]
    assert Decimal(str(sum_before["total_earned"])) == Decimal("150")

    _ok(
        await client.patch(
            f"/api/v1/cashback/cards/{card['id']}/rules/{rule['id']}",
            json={
                "min_purchase_amount": "2000",
                "recalculate_existing": True,
            },
            headers=headers,
        )
    )
    sum_after = _ok(await client.get("/api/v1/cashback/summary", headers=headers))["data"]
    assert Decimal(str(sum_after["total_earned"])) == Decimal("0")
