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


class CashbackRuleUpdate(BaseModel):
    cashback_percent: Decimal | None = Field(default=None, gt=0, le=100)
    monthly_limit: Decimal | None = Field(default=None, gt=0)
    min_purchase_amount: Decimal | None = Field(
        default=None,
        gt=0,
        description="Минимальная сумма покупки; null — сбросить порог.",
    )
    start_date: date | None = None
    end_date: date | None = None
    recalculate_existing: bool = Field(
        default=False,
        description="Пересчитать кэшбэк для подходящих расходов в категории правила.",
    )


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


class CashbackRuleUpdateResponse(BaseModel):
    rule: CashbackRuleResponse
    recalculated_transactions: int = 0


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
    is_manual: bool = False
    model_config = {"from_attributes": True}


class CashbackManualSet(BaseModel):
    amount: Decimal = Field(ge=0, description="Сумма кэшбэка; 0 — удалить начисление.")
    card_id: str | None = Field(
        default=None,
        description="Карта для начисления; если не указана — карта из транзакции.",
    )
