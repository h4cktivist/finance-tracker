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


class BudgetRecommendationItem(BaseModel):
    category_id: str
    category_name: str
    recommendation_type: str
    suggested_amount_limit: Decimal
    suggested_period_type: BudgetPeriodType
    avg_monthly_spent: Decimal
    max_monthly_spent: Decimal
    transaction_count: int
    months_with_activity: int
    existing_budget_id: str | None
    current_amount_limit: Decimal | None
    reason: str


class BudgetRecommendationsResponse(BaseModel):
    items: list[BudgetRecommendationItem]
    period_from: date
    period_to: date
    months_analyzed: int
