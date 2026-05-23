from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient


async def _auth_headers(client: AsyncClient) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register", json={"email": "txuser@example.com", "password": "securepass123"}
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": "txuser@example.com", "password": "securepass123"}
    )
    token = login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_expense_and_balance(client: AsyncClient):
    headers = await _auth_headers(client)
    account_resp = await client.post(
        "/api/v1/accounts",
        json={"name": "Wallet", "type": "cash", "initial_balance": "100"},
        headers=headers,
    )
    assert account_resp.status_code == 200
    account_id = account_resp.json()["data"]["id"]
    cat_resp = await client.post(
        "/api/v1/categories", json={"name": "Food", "type": "expense"}, headers=headers
    )
    category_id = cat_resp.json()["data"]["id"]
    tx_resp = await client.post(
        "/api/v1/transactions",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "25.50",
            "transaction_date": date.today().isoformat(),
        },
        headers=headers,
    )
    assert tx_resp.status_code == 200
    balance_resp = await client.get(f"/api/v1/accounts/{account_id}", headers=headers)
    balance = Decimal(str(balance_resp.json()["data"]["balance"]))
    assert balance == Decimal("74.50")
