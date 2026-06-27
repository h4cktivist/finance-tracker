from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class BrokerCashBalance(BaseModel):
    currency: str
    amount: Decimal


class BrokerPosition(BaseModel):
    symbol: str
    name: str | None
    asset_class: str | None
    quantity: Decimal
    average_price: Decimal
    average_price_percent: Decimal | None
    current_price: Decimal
    current_price_percent: Decimal | None
    market_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_percent: float
    daily_pnl: Decimal
    weight_percent: float


class BrokerAllocationItem(BaseModel):
    asset_class: str
    market_value: Decimal
    weight_percent: float


class BrokerIncomeBreakdown(BaseModel):
    coupon: Decimal
    dividend: Decimal
    redemption: Decimal
    lending: Decimal
    other: Decimal
    commission: Decimal
    total_return: Decimal
    period_from: datetime


class BrokerTransaction(BaseModel):
    id: str
    timestamp: datetime
    kind: str
    name: str
    symbol: str | None
    amount: Decimal
    currency: str


class BrokerPortfolio(BaseModel):
    account_id: str
    status: str
    equity: Decimal
    unrealized_pnl: Decimal
    daily_pnl: Decimal
    cash: list[BrokerCashBalance]
    positions: list[BrokerPosition]
    allocation: list[BrokerAllocationItem]
    income: BrokerIncomeBreakdown
    transactions: list[BrokerTransaction]
    updated_at: datetime


class BrokerRecommendationsResponse(BaseModel):
    account_id: str
    content: str
