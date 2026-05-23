from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.account import AccountType


class AccountCreate(BaseModel):
    name: str = Field(max_length=255)
    type: AccountType
    initial_balance: Decimal = Field(default=Decimal("0"), ge=0)


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    type: AccountType | None = None


class AccountResponse(BaseModel):
    id: str
    user_id: str
    name: str
    type: AccountType
    initial_balance: Decimal
    balance: Decimal | None = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
