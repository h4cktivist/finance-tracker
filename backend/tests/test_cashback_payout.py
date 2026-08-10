"""Кэшбэк: начисление накопленного за прошлый месяц как доходной транзакции."""

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.services.cashback import previous_period_month


def _ok(resp, expected_status: int = 200) -> dict:
    assert resp.status_code == expected_status, (
        f"{resp.request.method} {resp.request.url} -> {resp.status_code}: {resp.text}"
    )
    return resp.json()


async def _auth_headers(client: AsyncClient) -> dict:
    email = f"payout-{id(client)}@example.com"
    password = "secret12345"
    _ok(await client.post("/api/v1/auth/register", json={"email": email, "password": password}))
    login = _ok(
        await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    )
    return {"Authorization": f"Bearer {login['data']['access_token']}"}


def _last_month_day() -> date:
    year, month = (int(p) for p in previous_period_month().split("-"))
    return date(year, month, 15)


async def _setup_card_with_accrual(client: AsyncClient, headers: dict) -> tuple[dict, dict]:
    """Карта с расходом в прошлом месяце и 10% кэшбэка — накоплено 100."""
    account = _ok(
        await client.post(
            "/api/v1/accounts",
            json={"name": "CardAcc", "type": "credit", "initial_balance": "0"},
            headers=headers,
        )
    )["data"]
    category = _ok(
        await client.post(
            "/api/v1/categories",
            json={"name": "Food", "type": "expense"},
            headers=headers,
        )
    )["data"]
    card = _ok(
        await client.post(
            "/api/v1/cashback/cards",
            json={"account_id": account["id"], "name": "Visa"},
            headers=headers,
        )
    )["data"]
    spend_date = _last_month_day()
    _ok(
        await client.post(
            f"/api/v1/cashback/cards/{card['id']}/rules",
            json={
                "category_id": category["id"],
                "cashback_percent": "10",
                "start_date": spend_date.replace(day=1).isoformat(),
            },
            headers=headers,
        )
    )
    tx = _ok(
        await client.post(
            "/api/v1/transactions",
            json={
                "account_id": account["id"],
                "category_id": category["id"],
                "type": "expense",
                "amount": "1000",
                "transaction_date": spend_date.isoformat(),
                "card_id": card["id"],
            },
            headers=headers,
        )
    )["data"]
    assert Decimal(str(tx["cashback_amount"])) == Decimal("100")
    return account, card


@pytest.mark.asyncio
async def test_payout_preview_returns_last_month_accrual(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    _, card = await _setup_card_with_accrual(client, headers)

    preview = _ok(await client.get("/api/v1/cashback/payout/preview", headers=headers))["data"]
    assert preview["period_month"] == previous_period_month()
    entry = next(c for c in preview["cards"] if c["card_id"] == card["id"])
    assert Decimal(str(entry["accrued_amount"])) == Decimal("100")
    assert entry["already_paid_out"] is False


@pytest.mark.asyncio
async def test_payout_creates_income_transaction_in_cashback_category(
    client: AsyncClient,
) -> None:
    headers = await _auth_headers(client)
    account, card = await _setup_card_with_accrual(client, headers)

    payout = _ok(
        await client.post(
            "/api/v1/cashback/payout",
            json={"card_id": card["id"]},
            headers=headers,
        )
    )["data"]
    assert Decimal(str(payout["amount"])) == Decimal("100")
    assert payout["period_month"] == previous_period_month()

    tx = _ok(
        await client.get(f"/api/v1/transactions/{payout['transaction_id']}", headers=headers)
    )["data"]
    assert tx["type"] == "income"
    assert Decimal(str(tx["amount"])) == Decimal("100")
    assert tx["account_id"] == account["id"]
    assert tx["transaction_date"] == date.today().isoformat()

    categories = _ok(await client.get("/api/v1/categories", headers=headers))["data"]
    cashback_cat = next(c for c in categories if c["id"] == tx["category_id"])
    assert cashback_cat["name"] == "Кэшбэк"
    assert cashback_cat["type"] == "income"

    preview = _ok(await client.get("/api/v1/cashback/payout/preview", headers=headers))["data"]
    entry = next(c for c in preview["cards"] if c["card_id"] == card["id"])
    assert entry["already_paid_out"] is True


@pytest.mark.asyncio
async def test_payout_accepts_edited_amount(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    _, card = await _setup_card_with_accrual(client, headers)

    payout = _ok(
        await client.post(
            "/api/v1/cashback/payout",
            json={"card_id": card["id"], "amount": "137.50"},
            headers=headers,
        )
    )["data"]
    assert Decimal(str(payout["amount"])) == Decimal("137.50")

    tx = _ok(
        await client.get(f"/api/v1/transactions/{payout['transaction_id']}", headers=headers)
    )["data"]
    assert Decimal(str(tx["amount"])) == Decimal("137.50")


@pytest.mark.asyncio
async def test_payout_twice_for_same_period_conflicts(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    _, card = await _setup_card_with_accrual(client, headers)

    first = _ok(
        await client.post(
            "/api/v1/cashback/payout", json={"card_id": card["id"]}, headers=headers
        )
    )["data"]
    _ok(
        await client.post(
            "/api/v1/cashback/payout", json={"card_id": card["id"]}, headers=headers
        ),
        409,
    )

    # После удаления транзакции выплату можно провести заново.
    _ok(await client.delete(f"/api/v1/transactions/{first['transaction_id']}", headers=headers))
    _ok(
        await client.post(
            "/api/v1/cashback/payout", json={"card_id": card["id"]}, headers=headers
        )
    )


@pytest.mark.asyncio
async def test_payout_without_accrual_is_rejected(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    account = _ok(
        await client.post(
            "/api/v1/accounts",
            json={"name": "Wallet", "type": "cash", "initial_balance": "0"},
            headers=headers,
        )
    )["data"]
    card = _ok(
        await client.post(
            "/api/v1/cashback/cards",
            json={"account_id": account["id"], "name": "MC"},
            headers=headers,
        )
    )["data"]
    _ok(
        await client.post(
            "/api/v1/cashback/payout", json={"card_id": card["id"]}, headers=headers
        ),
        422,
    )
