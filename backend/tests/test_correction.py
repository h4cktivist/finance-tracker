from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient


async def _setup(client: AsyncClient) -> tuple[dict[str, str], str, str]:
    await client.post(
        "/api/v1/auth/register", json={"email": "corruser@example.com", "password": "securepass123"}
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": "corruser@example.com", "password": "securepass123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    acc = await client.post(
        "/api/v1/accounts",
        json={"name": "W", "type": "cash", "initial_balance": "1000"},
        headers=headers,
    )
    cat = await client.post(
        "/api/v1/categories", json={"name": "Food", "type": "expense"}, headers=headers
    )
    return (headers, acc.json()["data"]["id"], cat.json()["data"]["id"])


@pytest.mark.asyncio
async def test_correction_replaces_balance(client: AsyncClient):
    headers, acc_id, cat_id = await _setup(client)
    tx = await client.post(
        "/api/v1/transactions",
        json={
            "account_id": acc_id,
            "category_id": cat_id,
            "type": "expense",
            "amount": "100",
            "transaction_date": date.today().isoformat(),
        },
        headers=headers,
    )
    tx_id = tx.json()["data"]["id"]
    balance_after_first = await client.get(f"/api/v1/accounts/{acc_id}", headers=headers)
    assert Decimal(str(balance_after_first.json()["data"]["balance"])) == Decimal("900")
    correction = await client.post(
        f"/api/v1/transactions/{tx_id}/correct",
        json={"reason": "wrong amount", "new_amount": "75"},
        headers=headers,
    )
    assert correction.status_code == 200
    corrected = correction.json()["data"]
    assert corrected["correction_of_id"] == tx_id
    assert Decimal(str(corrected["amount"])) == Decimal("75")
    final_balance = await client.get(f"/api/v1/accounts/{acc_id}", headers=headers)
    assert Decimal(str(final_balance.json()["data"]["balance"])) == Decimal("925")
