from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.transaction import TransactionType


class TransactionCreate(BaseModel):
    account_id: str
    category_id: str | None = None
    type: TransactionType
    amount: Decimal = Field(gt=0)
    description: str | None = Field(default=None, max_length=500)
    merchant_name: str | None = Field(default=None, max_length=255)
    transaction_date: date
    notes: str | None = None
    tag_ids: list[str] = Field(default_factory=list)
    target_account_id: str | None = None
    card_id: str | None = None

    @model_validator(mode="after")
    def validate_transfer(self) -> "TransactionCreate":
        if self.type == TransactionType.TRANSFER and (not self.target_account_id):
            raise ValueError("target_account_id is required for transfers")
        if self.type != TransactionType.TRANSFER and self.target_account_id:
            raise ValueError("target_account_id only allowed for transfers")
        return self


class TransactionUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=500)
    merchant_name: str | None = Field(default=None, max_length=255)
    notes: str | None = None
    tag_ids: list[str] | None = None


class CorrectionCreate(BaseModel):
    reason: str = Field(max_length=500)
    new_amount: Decimal | None = Field(default=None, gt=0)
    new_account_id: str | None = None
    new_category_id: str | None = None


class TransactionResponse(BaseModel):
    id: str
    user_id: str
    account_id: str
    category_id: str | None
    type: TransactionType
    amount: Decimal
    description: str | None
    merchant_name: str | None
    transaction_date: date
    notes: str | None
    transfer_group_id: str | None
    correction_of_id: str | None
    card_id: str | None
    tag_ids: list[str] = Field(default_factory=list)
    cashback_amount: Decimal | None = Field(
        default=None,
        description="Начисленный кэшбэк (сумма accrued); только для расходов.",
    )
    cashback_is_manual: bool | None = Field(
        default=None,
        description="Кэшбэк задан вручную (не пересчитывается автоматически).",
    )
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    pages: int
