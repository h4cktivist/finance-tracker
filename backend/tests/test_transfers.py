from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient


async def _auth_headers(client: AsyncClient, suffix: str = "") -> dict[str, str]:
    email = f"transferuser{suffix}@example.com"
    await client.post("/api/v1/auth/register", json={"email": email, "password": "securepass123"})
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "securepass123"}
    )
    token = login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_transfer_balances(client: AsyncClient):
    headers = await _auth_headers(client)
    src = await client.post(
        "/api/v1/accounts",
        json={"name": "Source", "type": "cash", "initial_balance": "500"},
        headers=headers,
    )
    src_id = src.json()["data"]["id"]
    dst = await client.post(
        "/api/v1/accounts",
        json={"name": "Target", "type": "savings", "initial_balance": "0"},
        headers=headers,
    )
    dst_id = dst.json()["data"]["id"]
    resp = await client.post(
        "/api/v1/transactions",
        json={
            "account_id": src_id,
            "target_account_id": dst_id,
            "type": "transfer",
            "amount": "150.00",
            "transaction_date": date.today().isoformat(),
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert isinstance(resp.json()["data"], list)
    assert len(resp.json()["data"]) == 2
    src_balance = await client.get(f"/api/v1/accounts/{src_id}", headers=headers)
    dst_balance = await client.get(f"/api/v1/accounts/{dst_id}", headers=headers)
    assert Decimal(str(src_balance.json()["data"]["balance"])) == Decimal("350.00")
    assert Decimal(str(dst_balance.json()["data"]["balance"])) == Decimal("150.00")


@pytest.mark.asyncio
async def test_transfer_to_same_account_rejected(client: AsyncClient):
    headers = await _auth_headers(client, suffix="-same")
    acc = await client.post(
        "/api/v1/accounts",
        json={"name": "Single", "type": "cash", "initial_balance": "100"},
        headers=headers,
    )
    acc_id = acc.json()["data"]["id"]
    resp = await client.post(
        "/api/v1/transactions",
        json={
            "account_id": acc_id,
            "target_account_id": acc_id,
            "type": "transfer",
            "amount": "10",
            "transaction_date": date.today().isoformat(),
        },
        headers=headers,
    )
    assert resp.status_code in (400, 422)
