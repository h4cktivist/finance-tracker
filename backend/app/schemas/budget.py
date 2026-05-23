from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.budget import BudgetPeriodType


class BudgetCreate(BaseModel):
    category_id: str
    amount_limit: Decimal = Field(gt=0)
    period_type: BudgetPeriodType
    start_date: date
    end_date: date | None = None
    rollover_enabled: bool = False


class BudgetUpdate(BaseModel):
    amount_limit: Decimal | None = Field(default=None, gt=0)
    end_date: date | None = None
    rollover_enabled: bool | None = None


class BudgetResponse(BaseModel):
    id: str
    user_id: str
    category_id: str
    amount_limit: Decimal
    period_type: BudgetPeriodType
    start_date: date
    end_date: date | None
    rollover_enabled: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class BudgetStatusResponse(BaseModel):
    budget_id: str
    spent: Decimal
    remaining: Decimal
    percent_used: float
    days_until_exceed: int | None
    is_exceeded: bool
