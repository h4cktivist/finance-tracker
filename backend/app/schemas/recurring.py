from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.recurring import RecurringFrequency
from app.models.transaction import TransactionType


class RecurringCreate(BaseModel):
    frequency: RecurringFrequency
    interval: int = Field(default=1, ge=1)
    start_date: date
    end_date: date | None = None
    account_id: str
    category_id: str | None = None
    type: TransactionType
    amount: Decimal = Field(gt=0)
    description: str | None = None
    merchant_name: str | None = None
    notes: str | None = None


class RecurringUpdate(BaseModel):
    is_active: bool | None = None
    end_date: date | None = None
    amount: Decimal | None = Field(default=None, gt=0)


class RecurringResponse(BaseModel):
    id: str
    user_id: str
    frequency: RecurringFrequency
    interval: int
    start_date: date
    end_date: date | None
    next_execution_date: date
    is_active: bool
    account_id: str
    category_id: str | None
    type: TransactionType
    amount: Decimal
    description: str | None
    created_at: datetime
    model_config = {"from_attributes": True}
