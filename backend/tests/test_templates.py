"""Шаблоны платежей: создание из транзакции, применение, управление."""

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient


def _ok(resp, expected_status: int = 200) -> dict:
    assert (
        resp.status_code == expected_status
    ), f"{resp.request.method} {resp.request.url} -> {resp.status_code}: {resp.text}"
    return resp.json()


async def _auth_headers(client: AsyncClient, suffix: str = "") -> dict:
    email = f"templates{suffix}-{id(client)}@example.com"
    password = "secret12345"
    _ok(await client.post("/api/v1/auth/register", json={"email": email, "password": password}))
    login = _ok(
        await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    )
    return {"Authorization": f"Bearer {login['data']['access_token']}"}


async def _account(client: AsyncClient, headers: dict, name: str, balance: str = "0") -> str:
    return _ok(
        await client.post(
            "/api/v1/accounts",
            json={"name": name, "type": "cash", "initial_balance": balance},
            headers=headers,
        )
    )["data"]["id"]


async def _balance(client: AsyncClient, headers: dict, account_id: str) -> Decimal:
    data = _ok(await client.get(f"/api/v1/accounts/{account_id}", headers=headers))["data"]
    return Decimal(str(data["balance"]))


@pytest.mark.asyncio
async def test_template_from_expense_and_apply(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    account_id = await _account(client, headers, "Карта", "1000")
    category_id = _ok(
        await client.post(
            "/api/v1/categories", json={"name": "Связь", "type": "expense"}, headers=headers
        )
    )["data"]["id"]
    tag_id = _ok(await client.post("/api/v1/tags", json={"name": "мобила"}, headers=headers))[
        "data"
    ]["id"]
    tx = _ok(
        await client.post(
            "/api/v1/transactions",
            json={
                "account_id": account_id,
                "category_id": category_id,
                "type": "expense",
                "amount": "450.00",
                "description": "Оплата телефона",
                "merchant_name": "МТС",
                "notes": "тариф",
                "tag_ids": [tag_id],
                "transaction_date": "2026-01-10",
            },
            headers=headers,
        )
    )["data"]

    template = _ok(
        await client.post(f"/api/v1/templates/from-transaction/{tx['id']}", headers=headers)
    )["data"]
    assert template["name"] == "Оплата телефона"
    assert template["type"] == "expense"
    assert Decimal(template["amount"]) == Decimal("450.00")
    assert template["account_id"] == account_id
    assert template["category_id"] == category_id
    assert template["merchant_name"] == "МТС"
    assert template["notes"] == "тариф"
    assert template["tag_ids"] == [tag_id]

    templates = _ok(await client.get("/api/v1/templates", headers=headers))["data"]
    assert [t["id"] for t in templates] == [template["id"]]

    created = _ok(await client.post(f"/api/v1/templates/{template['id']}/apply", headers=headers))[
        "data"
    ]
    assert created["id"] != tx["id"]
    assert created["transaction_date"] == date.today().isoformat()
    assert created["category_id"] == category_id
    assert created["description"] == "Оплата телефона"
    assert created["tag_ids"] == [tag_id]
    assert await _balance(client, headers, account_id) == Decimal("100.00")


@pytest.mark.asyncio
async def test_apply_with_overrides(client: AsyncClient) -> None:
    headers = await _auth_headers(client, "-override")
    account_id = await _account(client, headers, "Нал")
    template = _ok(
        await client.post(
            "/api/v1/templates",
            json={"name": "Зарплата", "account_id": account_id, "type": "income", "amount": "100"},
            headers=headers,
        )
    )["data"]
    created = _ok(
        await client.post(
            f"/api/v1/templates/{template['id']}/apply",
            json={"transaction_date": "2026-02-01", "amount": "250.50"},
            headers=headers,
        )
    )["data"]
    assert created["transaction_date"] == "2026-02-01"
    assert Decimal(created["amount"]) == Decimal("250.50")
    assert await _balance(client, headers, account_id) == Decimal("250.50")


@pytest.mark.asyncio
async def test_template_from_transfer_either_leg(client: AsyncClient) -> None:
    headers = await _auth_headers(client, "-transfer")
    src = await _account(client, headers, "Source", "500")
    dst = await _account(client, headers, "Target")
    legs = _ok(
        await client.post(
            "/api/v1/transactions",
            json={
                "account_id": src,
                "target_account_id": dst,
                "type": "transfer",
                "amount": "100",
                "transaction_date": "2026-01-05",
            },
            headers=headers,
        )
    )["data"]

    for leg in legs:
        template = _ok(
            await client.post(f"/api/v1/templates/from-transaction/{leg['id']}", headers=headers)
        )["data"]
        assert template["account_id"] == src
        assert template["target_account_id"] == dst
        # Автоописание «Transfer to …» не переносится в шаблон.
        assert template["description"] is None

    applied = _ok(await client.post(f"/api/v1/templates/{template['id']}/apply", headers=headers))[
        "data"
    ]
    assert isinstance(applied, list) and len(applied) == 2
    assert await _balance(client, headers, src) == Decimal("300")
    assert await _balance(client, headers, dst) == Decimal("200")


@pytest.mark.asyncio
async def test_apply_skips_deleted_category(client: AsyncClient) -> None:
    headers = await _auth_headers(client, "-deleted-cat")
    account_id = await _account(client, headers, "Карта")
    category_id = _ok(
        await client.post(
            "/api/v1/categories", json={"name": "Кафе", "type": "expense"}, headers=headers
        )
    )["data"]["id"]
    template = _ok(
        await client.post(
            "/api/v1/templates",
            json={
                "name": "Кофе",
                "account_id": account_id,
                "category_id": category_id,
                "type": "expense",
                "amount": "250",
            },
            headers=headers,
        )
    )["data"]
    _ok(await client.delete(f"/api/v1/categories/{category_id}", headers=headers))

    created = _ok(await client.post(f"/api/v1/templates/{template['id']}/apply", headers=headers))[
        "data"
    ]
    assert created["category_id"] is None


@pytest.mark.asyncio
async def test_rename_and_delete_template(client: AsyncClient) -> None:
    headers = await _auth_headers(client, "-crud")
    account_id = await _account(client, headers, "Карта")
    template = _ok(
        await client.post(
            "/api/v1/templates",
            json={"name": "Old", "account_id": account_id, "type": "expense", "amount": "10"},
            headers=headers,
        )
    )["data"]
    updated = _ok(
        await client.patch(
            f"/api/v1/templates/{template['id']}",
            json={"name": "New", "amount": "20"},
            headers=headers,
        )
    )["data"]
    assert updated["name"] == "New"
    assert Decimal(updated["amount"]) == Decimal("20")

    _ok(await client.delete(f"/api/v1/templates/{template['id']}", headers=headers))
    assert _ok(await client.get("/api/v1/templates", headers=headers))["data"] == []
    _ok(await client.post(f"/api/v1/templates/{template['id']}/apply", headers=headers), 404)


@pytest.mark.asyncio
async def test_foreign_template_is_not_accessible(client: AsyncClient) -> None:
    owner = await _auth_headers(client, "-owner")
    stranger = await _auth_headers(client, "-stranger")
    account_id = await _account(client, owner, "Карта")
    template = _ok(
        await client.post(
            "/api/v1/templates",
            json={"name": "Мой", "account_id": account_id, "type": "expense", "amount": "10"},
            headers=owner,
        )
    )["data"]
    _ok(await client.post(f"/api/v1/templates/{template['id']}/apply", headers=stranger), 404)
    _ok(await client.delete(f"/api/v1/templates/{template['id']}", headers=stranger), 404)
    assert _ok(await client.get("/api/v1/templates", headers=stranger))["data"] == []
