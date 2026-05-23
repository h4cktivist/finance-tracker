from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models.budget import Budget, BudgetPeriodType
from app.services.budget import BudgetService


@pytest.mark.asyncio
async def test_budget_status_calculation():
    session = AsyncMock()
    service = BudgetService(session)
    service.repo = AsyncMock()
    service.tx_repo = AsyncMock()
    service.notifications = AsyncMock()
    budget = Budget(
        id=uuid4(),
        user_id=uuid4(),
        category_id=uuid4(),
        amount_limit=Decimal("1000"),
        period_type=BudgetPeriodType.MONTHLY,
        start_date=date.today().replace(day=1),
        end_date=None,
        rollover_enabled=False,
    )
    service.repo.get_by_id_for_user = AsyncMock(return_value=budget)
    service.tx_repo.sum_by_category = AsyncMock(return_value=400.0)
    status = await service.get_status(budget.user_id, budget.id)
    assert status.spent == Decimal("400")
    assert status.remaining == Decimal("600")
    assert status.is_exceeded is False
    assert status.percent_used == 40.0
