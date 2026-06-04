from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient

EMAIL = "fullapi@example.com"
PASSWORD = "supersecret123"


def _ok(resp, expected_status: int = 200) -> dict:
    assert (
        resp.status_code == expected_status
    ), f"{resp.request.method} {resp.request.url} -> {resp.status_code}: {resp.text}"
    return resp.json()


async def _register_and_login(client: AsyncClient) -> tuple[str, str, dict[str, str]]:
    reg = await client.post("/api/v1/auth/register", json={"email": EMAIL, "password": PASSWORD})
    body = _ok(reg)
    user_id = body["data"]["id"]
    login = await client.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    tokens = _ok(login)["data"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    return (user_id, tokens["refresh_token"], headers)


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    body = _ok(await client.get("/health"))
    assert body["data"] == {"status": "ok"}


@pytest.mark.asyncio
async def test_full_api_surface(client: AsyncClient):
    _, refresh_token, headers = await _register_and_login(client)
    refresh_resp = _ok(
        await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    )
    new_refresh = refresh_resp["data"]["refresh_token"]
    headers = {"Authorization": f"Bearer {refresh_resp['data']['access_token']}"}
    acc_resp = _ok(
        await client.post(
            "/api/v1/accounts",
            json={"name": "Main Wallet", "type": "cash", "initial_balance": "1000"},
            headers=headers,
        )
    )
    account_id = acc_resp["data"]["id"]
    savings_resp = _ok(
        await client.post(
            "/api/v1/accounts",
            json={"name": "Savings", "type": "savings", "initial_balance": "500"},
            headers=headers,
        )
    )
    savings_id = savings_resp["data"]["id"]
    card_acc_resp = _ok(
        await client.post(
            "/api/v1/accounts",
            json={"name": "Credit", "type": "credit", "initial_balance": "0"},
            headers=headers,
        )
    )
    card_account_id = card_acc_resp["data"]["id"]
    accounts = _ok(await client.get("/api/v1/accounts", headers=headers))
    assert len(accounts["data"]) == 3
    assert all("balance" in a for a in accounts["data"])
    _ok(await client.get(f"/api/v1/accounts/{account_id}", headers=headers))
    _ok(
        await client.patch(
            f"/api/v1/accounts/{account_id}",
            json={"name": "Main Wallet (renamed)"},
            headers=headers,
        )
    )
    food = _ok(
        await client.post(
            "/api/v1/categories", json={"name": "Food", "type": "expense"}, headers=headers
        )
    )["data"]
    food_id = food["id"]
    groceries = _ok(
        await client.post(
            "/api/v1/categories",
            json={"name": "Groceries", "type": "expense", "parent_category_id": food_id},
            headers=headers,
        )
    )["data"]
    groceries_id = groceries["id"]
    salary = _ok(
        await client.post(
            "/api/v1/categories",
            json={"name": "Salary", "type": "income", "is_essential": True},
            headers=headers,
        )
    )["data"]
    salary_id = salary["id"]
    flat_cats = _ok(await client.get("/api/v1/categories", headers=headers))
    assert len(flat_cats["data"]) == 3
    tree = _ok(await client.get("/api/v1/categories/tree", headers=headers))
    food_node = next(n for n in tree["data"] if n["id"] == food_id)
    assert len(food_node["children"]) == 1
    _ok(
        await client.patch(
            f"/api/v1/categories/{groceries_id}", json={"color": "#00ff00"}, headers=headers
        )
    )
    work_tag = _ok(
        await client.post(
            "/api/v1/tags", json={"name": "work", "color": "#0066cc"}, headers=headers
        )
    )["data"]
    work_tag_id = work_tag["id"]
    fun_tag = _ok(await client.post("/api/v1/tags", json={"name": "fun"}, headers=headers))["data"]
    fun_tag_id = fun_tag["id"]
    tags = _ok(await client.get("/api/v1/tags", headers=headers))
    assert len(tags["data"]) == 2
    _ok(
        await client.patch(f"/api/v1/tags/{fun_tag_id}", json={"color": "#ff00ff"}, headers=headers)
    )
    card = _ok(
        await client.post(
            "/api/v1/cashback/cards",
            json={
                "account_id": card_account_id,
                "name": "Platinum",
                "bank_name": "MyBank",
                "last_digits": "1234",
            },
            headers=headers,
        )
    )["data"]
    card_id = card["id"]
    rule = _ok(
        await client.post(
            f"/api/v1/cashback/cards/{card_id}/rules",
            json={
                "category_id": groceries_id,
                "cashback_percent": "5",
                "monthly_limit": "1000",
                "start_date": date.today().isoformat(),
            },
            headers=headers,
        )
    )["data"]
    assert rule["card_id"] == card_id
    cards = _ok(await client.get("/api/v1/cashback/cards", headers=headers))
    assert len(cards["data"]) == 1
    rules = _ok(await client.get(f"/api/v1/cashback/cards/{card_id}/rules", headers=headers))
    assert len(rules["data"]) == 1
    recs = _ok(
        await client.get(
            "/api/v1/cashback/recommendations",
            params={"category_id": groceries_id},
            headers=headers,
        )
    )
    assert len(recs["data"]) >= 1
    today = date.today()
    income_tx = _ok(
        await client.post(
            "/api/v1/transactions",
            json={
                "account_id": account_id,
                "category_id": salary_id,
                "type": "income",
                "amount": "5000",
                "transaction_date": today.isoformat(),
                "description": "Monthly salary",
                "tag_ids": [work_tag_id],
            },
            headers=headers,
        )
    )["data"]
    assert work_tag_id in income_tx["tag_ids"]
    expense_tx = _ok(
        await client.post(
            "/api/v1/transactions",
            json={
                "account_id": card_account_id,
                "category_id": groceries_id,
                "type": "expense",
                "amount": "150.00",
                "transaction_date": today.isoformat(),
                "merchant_name": "Local Store",
                "card_id": card_id,
                "tag_ids": [fun_tag_id],
            },
            headers=headers,
        )
    )["data"]
    expense_tx_id = expense_tx["id"]
    transfer = _ok(
        await client.post(
            "/api/v1/transactions",
            json={
                "account_id": account_id,
                "target_account_id": savings_id,
                "type": "transfer",
                "amount": "200",
                "transaction_date": today.isoformat(),
            },
            headers=headers,
        )
    )
    assert isinstance(transfer["data"], list)
    assert len(transfer["data"]) == 2
    main_balance = Decimal(
        str(
            _ok(await client.get(f"/api/v1/accounts/{account_id}", headers=headers))["data"][
                "balance"
            ]
        )
    )
    assert main_balance == Decimal("5800")
    savings_balance = Decimal(
        str(
            _ok(await client.get(f"/api/v1/accounts/{savings_id}", headers=headers))["data"][
                "balance"
            ]
        )
    )
    assert savings_balance == Decimal("700")
    list_tx = _ok(
        await client.get(
            "/api/v1/transactions", params={"page": 1, "page_size": 50}, headers=headers
        )
    )["data"]
    assert list_tx["total"] >= 4
    expense_only = _ok(
        await client.get("/api/v1/transactions", params={"type": "expense"}, headers=headers)
    )["data"]
    assert expense_only["total"] == 1
    by_tag = _ok(
        await client.get("/api/v1/transactions", params={"tag_id": work_tag_id}, headers=headers)
    )["data"]
    assert by_tag["total"] == 1
    _ok(await client.get(f"/api/v1/transactions/{expense_tx_id}", headers=headers))
    _ok(
        await client.patch(
            f"/api/v1/transactions/{expense_tx_id}",
            json={"notes": "Edited note", "tag_ids": [work_tag_id, fun_tag_id]},
            headers=headers,
        )
    )
    corrected = _ok(
        await client.post(
            f"/api/v1/transactions/{expense_tx_id}/correct",
            json={"reason": "Wrong amount", "new_amount": "125.00"},
            headers=headers,
        )
    )["data"]
    assert corrected["correction_of_id"] == expense_tx_id
    correction_tx_id = corrected["id"]
    rec = _ok(
        await client.post(
            "/api/v1/recurring",
            json={
                "frequency": "monthly",
                "interval": 1,
                "start_date": today.isoformat(),
                "account_id": account_id,
                "category_id": salary_id,
                "type": "income",
                "amount": "5000",
                "description": "Salary",
            },
            headers=headers,
        )
    )["data"]
    rec_id = rec["id"]
    _ok(await client.get("/api/v1/recurring", headers=headers))
    _ok(
        await client.patch(
            f"/api/v1/recurring/{rec_id}", json={"is_active": False}, headers=headers
        )
    )
    budget = _ok(
        await client.post(
            "/api/v1/budgets",
            json={
                "category_id": groceries_id,
                "amount_limit": "500",
                "period_type": "monthly",
                "start_date": today.replace(day=1).isoformat(),
            },
            headers=headers,
        )
    )["data"]
    budget_id = budget["id"]
    _ok(await client.get("/api/v1/budgets", headers=headers))
    status = _ok(await client.get(f"/api/v1/budgets/{budget_id}/status", headers=headers))["data"]
    assert "spent" in status and "remaining" in status
    _ok(
        await client.patch(
            f"/api/v1/budgets/{budget_id}", json={"amount_limit": "600"}, headers=headers
        )
    )
    _ok(await client.delete(f"/api/v1/budgets/{budget_id}", headers=headers))
    goal = _ok(
        await client.post(
            "/api/v1/goals",
            json={
                "name": "Vacation",
                "target_amount": "3000",
                "deadline": (today + timedelta(days=180)).isoformat(),
                "linked_account_id": savings_id,
            },
            headers=headers,
        )
    )["data"]
    goal_id = goal["id"]
    _ok(await client.get("/api/v1/goals", headers=headers))
    progress = _ok(await client.get(f"/api/v1/goals/{goal_id}/progress", headers=headers))["data"]
    assert progress["target_amount"] == "3000.00"
    _ok(
        await client.patch(
            f"/api/v1/goals/{goal_id}", json={"name": "Vacation 2026"}, headers=headers
        )
    )
    _ok(await client.get("/api/v1/cashback/summary", headers=headers))
    _ok(await client.get("/api/v1/cashback/missed", headers=headers))
    dash = _ok(await client.get("/api/v1/analytics/dashboard", headers=headers))["data"]
    assert "total_balance" in dash and "goals_progress" in dash
    stats = _ok(await client.get("/api/v1/analytics/statistics", headers=headers))["data"]
    assert "top_expense_categories" in stats
    heatmap = _ok(await client.get("/api/v1/analytics/heatmap", headers=headers))["data"]
    assert "days" in heatmap
    ratios = _ok(await client.get("/api/v1/analytics/ratios", headers=headers))["data"]
    assert "savings_rate" in ratios
    trends = _ok(await client.get("/api/v1/analytics/trends", headers=headers))["data"]
    assert "points" in trends and isinstance(trends["points"], list)
    notif_list = _ok(await client.get("/api/v1/notifications", headers=headers))["data"]
    assert notif_list["total"] >= 1
    notif_id = notif_list["items"][0]["id"]
    _ok(await client.patch(f"/api/v1/notifications/{notif_id}/read", headers=headers))
    marked_all = _ok(await client.post("/api/v1/notifications/read-all", headers=headers))["data"]
    assert "marked_read" in marked_all
    req = _ok(await client.post("/api/v1/auth/reset-password", json={"email": EMAIL}))
    assert "Dev token:" in req["message"]
    reset_token = req["message"].split("Dev token:")[1].strip()
    _ok(
        await client.post(
            "/api/v1/auth/reset-password",
            json={"email": EMAIL, "new_password": "anothersecret123", "reset_token": reset_token},
        )
    )
    bad_login = await client.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert bad_login.status_code == 401
    relogin = _ok(
        await client.post(
            "/api/v1/auth/login", json={"email": EMAIL, "password": "anothersecret123"}
        )
    )
    headers = {"Authorization": f"Bearer {relogin['data']['access_token']}"}
    new_refresh = relogin["data"]["refresh_token"]
    _ok(await client.delete(f"/api/v1/transactions/{correction_tx_id}", headers=headers))
    _ok(await client.delete(f"/api/v1/tags/{fun_tag_id}", headers=headers))
    _ok(await client.delete(f"/api/v1/categories/{groceries_id}", headers=headers))
    _ok(await client.delete(f"/api/v1/accounts/{savings_id}", headers=headers))
    _ok(await client.post("/api/v1/auth/logout", json={"refresh_token": new_refresh}))
    bad_refresh = await client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert bad_refresh.status_code in {401, 403}


@pytest.mark.asyncio
async def test_unauthorized_access_rejected(client: AsyncClient):
    routes = [
        ("GET", "/api/v1/accounts"),
        ("GET", "/api/v1/categories"),
        ("GET", "/api/v1/transactions"),
        ("GET", "/api/v1/tags"),
        ("GET", "/api/v1/budgets"),
        ("GET", "/api/v1/goals"),
        ("GET", "/api/v1/recurring"),
        ("GET", "/api/v1/cashback/cards"),
        ("GET", "/api/v1/cashback/summary"),
        ("GET", "/api/v1/analytics/dashboard"),
        ("GET", "/api/v1/notifications"),
    ]
    for method, path in routes:
        resp = await client.request(method, path)
        assert resp.status_code in {401, 403}, f"{method} {path} returned {resp.status_code}"


@pytest.mark.asyncio
async def test_validation_errors(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "validation@example.com", "password": "validpass123"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": "validation@example.com", "password": "validpass123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    bad_email = await client.post(
        "/api/v1/auth/register", json={"email": "not-an-email", "password": "x" * 10}
    )
    assert bad_email.status_code == 422
    short_pwd = await client.post(
        "/api/v1/auth/register", json={"email": "x@y.io", "password": "short"}
    )
    assert short_pwd.status_code == 422
    bad_amount = await client.post(
        "/api/v1/accounts",
        json={"name": "X", "type": "cash", "initial_balance": "-5"},
        headers=headers,
    )
    assert bad_amount.status_code == 422
    bad_type = await client.post(
        "/api/v1/accounts",
        json={"name": "X", "type": "spaceship", "initial_balance": "10"},
        headers=headers,
    )
    assert bad_type.status_code == 422
    acc = await client.post(
        "/api/v1/accounts",
        json={"name": "Acc", "type": "cash", "initial_balance": "0"},
        headers=headers,
    )
    account_id = acc.json()["data"]["id"]
    no_target = await client.post(
        "/api/v1/transactions",
        json={
            "account_id": account_id,
            "type": "transfer",
            "amount": "10",
            "transaction_date": date.today().isoformat(),
        },
        headers=headers,
    )
    assert no_target.status_code == 422
