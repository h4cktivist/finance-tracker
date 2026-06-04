from calendar import monthrange
from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.services.forecast import _parse_target_month


async def _auth_headers(client: AsyncClient, email: str) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "securepass123"}
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "securepass123"}
    )
    token = login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _next_month_str() -> str:
    today = date.today()
    if today.month == 12:
        return f"{today.year + 1}-01"
    return f"{today.year:04d}-{today.month + 1:02d}"


def _month_start_end(month_str: str) -> tuple[date, date]:
    year, mon = map(int, month_str.split("-"))
    last = monthrange(year, mon)[1]
    return date(year, mon, 1), date(year, mon, last)


def _history_month_tx_date(month_str: str) -> str:
    start, _ = _month_start_end(month_str)
    return start.isoformat()


@pytest.mark.asyncio
async def test_forecast_rejects_current_or_past_month(client: AsyncClient):
    headers = await _auth_headers(client, "forecast-past@example.com")
    current = date.today().strftime("%Y-%m")
    resp = await client.get(
        "/api/v1/analytics/forecast",
        headers=headers,
        params={"month": current},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_forecast_from_recurring_and_history(client: AsyncClient):
    headers = await _auth_headers(client, "forecast-main@example.com")
    account_id = (
        await client.post(
            "/api/v1/accounts",
            json={"name": "Wallet", "type": "cash", "initial_balance": "0"},
            headers=headers,
        )
    ).json()["data"]["id"]
    salary_cat = (
        await client.post(
            "/api/v1/categories", json={"name": "Зарплата", "type": "income"}, headers=headers
        )
    ).json()["data"]["id"]
    sub_cat = (
        await client.post(
            "/api/v1/categories", json={"name": "Подписки", "type": "expense"}, headers=headers
        )
    ).json()["data"]["id"]

    target = _next_month_str()
    y, m = map(int, target.split("-"))
    history = []
    for offset in (3, 2, 1):
        mm = m - offset
        yy = y
        while mm < 1:
            mm += 12
            yy -= 1
        history.append(f"{yy:04d}-{mm:02d}")

    for month_str in history:
        tx_date = _history_month_tx_date(month_str)
        await client.post(
            "/api/v1/transactions",
            json={
                "account_id": account_id,
                "category_id": salary_cat,
                "type": "income",
                "amount": "100000",
                "transaction_date": tx_date,
            },
            headers=headers,
        )
        await client.post(
            "/api/v1/transactions",
            json={
                "account_id": account_id,
                "category_id": sub_cat,
                "type": "expense",
                "amount": "5000",
                "transaction_date": tx_date,
            },
            headers=headers,
        )

    target_start, _ = _month_start_end(target)
    await client.post(
        "/api/v1/recurring",
        json={
            "account_id": account_id,
            "category_id": salary_cat,
            "type": "income",
            "amount": "80000",
            "frequency": "monthly",
            "interval": 1,
            "start_date": target_start.isoformat(),
        },
        headers=headers,
    )

    resp = await client.get(
        "/api/v1/analytics/forecast",
        headers=headers,
        params={"month": target},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["target_month"] == target
    assert Decimal(data["income_breakdown"]["recurring"]) == Decimal("80000")
    assert Decimal(data["expenses_breakdown"]["trend"]) == Decimal("5000")
    assert Decimal(data["income"]) == Decimal("180000")
    assert Decimal(data["expenses"]) == Decimal("5000")
    assert Decimal(data["cashflow"]) == Decimal("175000")
    assert data["confidence"] == "high"


@pytest.mark.asyncio
async def test_forecast_exclude_investments(client: AsyncClient):
    headers = await _auth_headers(client, "forecast-inv@example.com")
    account_id = (
        await client.post(
            "/api/v1/accounts",
            json={"name": "Wallet", "type": "cash", "initial_balance": "0"},
            headers=headers,
        )
    ).json()["data"]["id"]
    invest_id = (
        await client.post(
            "/api/v1/categories",
            json={"name": "Инвестиции", "type": "expense"},
            headers=headers,
        )
    ).json()["data"]["id"]

    target = _next_month_str()
    y, m = map(int, target.split("-"))
    mm = m - 1
    yy = y
    if mm < 1:
        mm = 12
        yy -= 1
    hist = f"{yy:04d}-{mm:02d}"
    await client.post(
        "/api/v1/transactions",
        json={
            "account_id": account_id,
            "category_id": invest_id,
            "type": "expense",
            "amount": "10000",
            "transaction_date": _history_month_tx_date(hist),
        },
        headers=headers,
    )

    target_start, _ = _month_start_end(target)
    await client.post(
        "/api/v1/recurring",
        json={
            "account_id": account_id,
            "category_id": invest_id,
            "type": "expense",
            "amount": "20000",
            "frequency": "monthly",
            "interval": 1,
            "start_date": target_start.isoformat(),
        },
        headers=headers,
    )

    all_fc = (
        await client.get(
            "/api/v1/analytics/forecast",
            headers=headers,
            params={"month": target},
        )
    ).json()["data"]
    filtered_fc = (
        await client.get(
            "/api/v1/analytics/forecast",
            headers=headers,
            params={"month": target, "exclude_investments": True},
        )
    ).json()["data"]

    assert Decimal(all_fc["expenses_breakdown"]["recurring"]) == Decimal("20000")
    assert Decimal(filtered_fc["expenses_breakdown"]["recurring"]) == Decimal("0")


def test_parse_target_month_defaults_to_next():
    today = date.today()
    y, m = _parse_target_month(None)
    if today.month == 12:
        assert (y, m) == (today.year + 1, 1)
    else:
        assert (y, m) == (today.year, today.month + 1)

