from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.transaction import TransactionType


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    account_id: str
    category_id: str | None = None
    type: TransactionType
    amount: Decimal = Field(gt=0)
    description: str | None = Field(default=None, max_length=500)
    merchant_name: str | None = Field(default=None, max_length=255)
    notes: str | None = None
    tag_ids: list[str] = Field(default_factory=list)
    target_account_id: str | None = None
    card_id: str | None = None

    @model_validator(mode="after")
    def validate_transfer(self) -> "TemplateCreate":
        if self.type == TransactionType.TRANSFER and (not self.target_account_id):
            raise ValueError("target_account_id is required for transfers")
        if self.type != TransactionType.TRANSFER and self.target_account_id:
            raise ValueError("target_account_id only allowed for transfers")
        return self


class TemplateFromTransaction(BaseModel):
    name: str | None = Field(default=None, max_length=255)


class TemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    amount: Decimal | None = Field(default=None, gt=0)


class TemplateApply(BaseModel):
    transaction_date: date | None = Field(
        default=None, description="Дата операции; по умолчанию — сегодня."
    )
    amount: Decimal | None = Field(default=None, gt=0, description="Переопределить сумму шаблона.")


class TemplateResponse(BaseModel):
    id: str
    name: str
    account_id: str
    target_account_id: str | None
    category_id: str | None
    card_id: str | None
    type: TransactionType
    amount: Decimal
    description: str | None
    merchant_name: str | None
    notes: str | None
    tag_ids: list[str]
    created_at: datetime
    model_config = {"from_attributes": True}
