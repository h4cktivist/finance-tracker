"""Карта магазинов: какие категории попадают в разбивку по мерчантам."""

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
    email = f"merchants-{id(client)}@example.com"
    password = "secret12345"
    _ok(await client.post("/api/v1/auth/register", json={"email": email, "password": password}))
    login = _ok(
        await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    )
    return {"Authorization": f"Bearer {login['data']['access_token']}"}


async def _category(client: AsyncClient, headers: dict, name: str) -> str:
    return _ok(
        await client.post(
            "/api/v1/categories", json={"name": name, "type": "expense"}, headers=headers
        )
    )["data"]["id"]


async def _expense(
    client: AsyncClient, headers: dict, account_id: str, category_id: str,
    merchant: str, amount: str,
) -> None:
    _ok(
        await client.post(
            "/api/v1/transactions",
            json={
                "account_id": account_id,
                "category_id": category_id,
                "type": "expense",
                "amount": amount,
                "merchant_name": merchant,
                "transaction_date": date.today().isoformat(),
            },
            headers=headers,
        )
    )


@pytest.mark.asyncio
async def test_personal_transfers_excluded_from_merchants_map(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    account_id = _ok(
        await client.post(
            "/api/v1/accounts",
            json={"name": "Wallet", "type": "cash", "initial_balance": "100000"},
            headers=headers,
        )
    )["data"]["id"]
    shops = await _category(client, headers, "Продукты")
    transfers = await _category(client, headers, "Переводы людям")

    await _expense(client, headers, account_id, shops, "Пятёрочка", "1500")
    await _expense(client, headers, account_id, transfers, "Иван И.", "9000")

    merchants = _ok(await client.get("/api/v1/analytics/merchants", headers=headers))["data"]
    names = [c["category_name"] for c in merchants["categories"]]
    assert "Продукты" in names
    assert "Переводы людям" not in names


@pytest.mark.asyncio
async def test_personal_transfers_excluded_regardless_of_investments_toggle(
    client: AsyncClient,
) -> None:
    """Исключение переводов не зависит от тумблера «без инвестиций»."""
    headers = await _auth_headers(client)
    account_id = _ok(
        await client.post(
            "/api/v1/accounts",
            json={"name": "Wallet", "type": "cash", "initial_balance": "100000"},
            headers=headers,
        )
    )["data"]["id"]
    shops = await _category(client, headers, "Кафе")
    transfers = await _category(client, headers, "Переводы людям")
    investments = await _category(client, headers, "Инвестиции")

    await _expense(client, headers, account_id, shops, "Кофейня", "800")
    await _expense(client, headers, account_id, transfers, "Пётр П.", "5000")
    await _expense(client, headers, account_id, investments, "Брокер", "20000")

    plain = _ok(await client.get("/api/v1/analytics/merchants", headers=headers))["data"]
    plain_names = [c["category_name"] for c in plain["categories"]]
    assert "Переводы людям" not in plain_names
    assert "Инвестиции" in plain_names

    filtered = _ok(
        await client.get(
            "/api/v1/analytics/merchants",
            params={"exclude_investments": True},
            headers=headers,
        )
    )["data"]
    filtered_names = [c["category_name"] for c in filtered["categories"]]
    assert "Переводы людям" not in filtered_names
    assert "Инвестиции" not in filtered_names
    assert "Кафе" in filtered_names


@pytest.mark.asyncio
async def test_transfers_category_of_another_user_does_not_hide_own_merchants(
    client: AsyncClient,
) -> None:
    """Исключение работает по категориям владельца, а не по чужим одноимённым."""
    first = await _auth_headers(client)
    await _category(client, first, "Переводы людям")

    email = f"merchants-second-{id(client)}@example.com"
    password = "secret12345"
    _ok(await client.post("/api/v1/auth/register", json={"email": email, "password": password}))
    login = _ok(
        await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    )
    second = {"Authorization": f"Bearer {login['data']['access_token']}"}

    account_id = _ok(
        await client.post(
            "/api/v1/accounts",
            json={"name": "Wallet", "type": "cash", "initial_balance": "50000"},
            headers=second,
        )
    )["data"]["id"]
    shops = await _category(client, second, "Аптека")
    await _expense(client, second, account_id, shops, "Ригла", "700")

    merchants = _ok(await client.get("/api/v1/analytics/merchants", headers=second))["data"]
    categories = merchants["categories"]
    assert [c["category_name"] for c in categories] == ["Аптека"]
    assert Decimal(str(categories[0]["total"])) == Decimal("700")
