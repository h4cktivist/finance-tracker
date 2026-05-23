from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.financial_goal import GoalStatus


class GoalCreate(BaseModel):
    name: str = Field(max_length=255)
    target_amount: Decimal = Field(gt=0)
    deadline: date | None = None
    linked_account_id: str | None = None


class GoalUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    target_amount: Decimal | None = Field(default=None, gt=0)
    deadline: date | None = None
    status: GoalStatus | None = None


class GoalResponse(BaseModel):
    id: str
    user_id: str
    name: str
    target_amount: Decimal
    current_amount: Decimal
    deadline: date | None
    linked_account_id: str | None
    status: GoalStatus
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class GoalProgressResponse(BaseModel):
    goal_id: str
    current_amount: Decimal
    target_amount: Decimal
    progress_percent: float
    remaining: Decimal
    status: GoalStatus
