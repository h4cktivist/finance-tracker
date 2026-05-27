from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.cashback import CashbackAccrualStatus


class CardCreate(BaseModel):
    account_id: str
    name: str = Field(max_length=255)
    bank_name: str | None = None
    last_digits: str | None = Field(default=None, max_length=4)


class CardResponse(BaseModel):
    id: str
    user_id: str
    account_id: str
    name: str
    bank_name: str | None
    last_digits: str | None
    model_config = {"from_attributes": True}


class CashbackRuleCreate(BaseModel):
    category_id: str
    cashback_percent: Decimal = Field(gt=0, le=100)
    monthly_limit: Decimal | None = Field(default=None, gt=0)
    min_purchase_amount: Decimal | None = Field(
        default=None,
        gt=0,
        description="Минимальная сумма покупки для начисления; None — без порога.",
    )
    start_date: date
    end_date: date | None = None


class CashbackRuleResponse(BaseModel):
    id: str
    card_id: str
    category_id: str
    cashback_percent: Decimal
    monthly_limit: Decimal | None
    min_purchase_amount: Decimal | None
    start_date: date
    end_date: date | None
    model_config = {"from_attributes": True}


class CashbackSummaryResponse(BaseModel):
    total_earned: Decimal
    period_month: str | None = None


class CashbackRecommendation(BaseModel):
    category_id: str
    best_card_id: str
    best_card_name: str
    cashback_percent: Decimal
    min_purchase_amount: Decimal | None = None


class CashbackAccrualResponse(BaseModel):
    id: str
    transaction_id: str
    card_id: str
    amount: Decimal
    period_month: str
    status: CashbackAccrualStatus
    model_config = {"from_attributes": True}
