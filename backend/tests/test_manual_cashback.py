"""Ручное редактирование кэшбэка за покупку."""

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient


def _ok(resp, expected_status: int = 200) -> dict:
    assert resp.status_code == expected_status, (
        f"{resp.request.method} {resp.request.url} -> {resp.status_code}: {resp.text}"
    )
    return resp.json()


async def _auth_headers(client: AsyncClient) -> dict:
    email = f"manual-{id(client)}@example.com"
    password = "secret12345"
    _ok(await client.post("/api/v1/auth/register", json={"email": email, "password": password}))
    login = _ok(
        await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    )
    return {"Authorization": f"Bearer {login['data']['access_token']}"}


@pytest.mark.asyncio
async def test_set_manual_cashback_overrides_auto_amount(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
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
    tx = _ok(
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
    )["data"]
    assert Decimal(str(tx["cashback_amount"])) == Decimal("100")

    updated = _ok(
        await client.put(
            f"/api/v1/transactions/{tx['id']}/cashback",
            json={"amount": "99"},
            headers=headers,
        )
    )["data"]
    assert Decimal(str(updated["amount"])) == Decimal("99")
    assert updated["is_manual"] is True

    tx_after = _ok(
        await client.get(f"/api/v1/transactions/{tx['id']}", headers=headers)
    )["data"]
    assert Decimal(str(tx_after["cashback_amount"])) == Decimal("99")
    assert tx_after["cashback_is_manual"] is True

    _ok(
        await client.patch(
            f"/api/v1/cashback/cards/{card['id']}/rules/{rule['id']}",
            json={"cashback_percent": "20", "recalculate_existing": True},
            headers=headers,
        )
    )
    tx_recalc = _ok(
        await client.get(f"/api/v1/transactions/{tx['id']}", headers=headers)
    )["data"]
    assert Decimal(str(tx_recalc["cashback_amount"])) == Decimal("99")


@pytest.mark.asyncio
async def test_delete_manual_cashback(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    acc = _ok(
        await client.post(
            "/api/v1/accounts",
            json={"name": "Wallet", "type": "cash", "initial_balance": "0"},
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
            json={"account_id": acc["id"], "name": "MC"},
            headers=headers,
        )
    )["data"]
    today = date.today().isoformat()
    tx = _ok(
        await client.post(
            "/api/v1/transactions",
            json={
                "account_id": acc["id"],
                "category_id": cat["id"],
                "type": "expense",
                "amount": "500",
                "transaction_date": today,
                "card_id": card["id"],
            },
            headers=headers,
        )
    )["data"]
    _ok(
        await client.put(
            f"/api/v1/transactions/{tx['id']}/cashback",
            json={"amount": "25"},
            headers=headers,
        )
    )
    _ok(
        await client.delete(f"/api/v1/transactions/{tx['id']}/cashback", headers=headers)
    )
    tx_after = _ok(
        await client.get(f"/api/v1/transactions/{tx['id']}", headers=headers)
    )["data"]
    assert tx_after["cashback_amount"] is None
