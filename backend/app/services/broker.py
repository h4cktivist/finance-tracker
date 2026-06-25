import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.core.exceptions import AppException
from app.schemas.broker import (
    BrokerAllocationItem,
    BrokerCashBalance,
    BrokerIncomeBreakdown,
    BrokerPortfolio,
    BrokerPosition,
    BrokerTransaction,
)
from app.services.finam_trade_api import FinamTradeApiClient

ASSET_TYPE_LABELS = {
    "EQUITIES": "Акции",
    "BONDS": "Облигации",
    "FUNDS": "Фонды",
    "ETF": "Фонды",
    "FUTURES": "Фьючерсы",
    "OPTIONS": "Опционы",
    "CURRENCIES": "Валюта",
}

TRANSACTIONS_LIMIT = 1000
RECENT_TRANSACTIONS_LIMIT = 30


class BrokerCredentialsMissingError(AppException):

    def __init__(self, message: str = "Заполните токен Finam и номер счёта в настройках") -> None:
        super().__init__(message=message, code="BROKER_NOT_CONFIGURED", status_code=400)


def _money(value: dict[str, Any] | None) -> Decimal:
    if not value or value.get("value") is None:
        return Decimal("0")
    return Decimal(str(value["value"]))


def _cash_amount(item: dict[str, Any]) -> Decimal:
    units = Decimal(str(item.get("units", "0")))
    nanos = Decimal(str(item.get("nanos", 0))) / Decimal("1000000000")
    return units + nanos


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _classify_transaction(category: str, name: str) -> str:
    if category == "DEPOSIT":
        return "deposit"
    if category == "WITHDRAWAL":
        return "withdrawal"
    if category == "COMMISSION":
        return "commission"
    if category == "INCOME":
        lname = name.lower()
        if "купон" in lname:
            return "coupon"
        if "дивиденд" in lname:
            return "dividend"
        if "погашен" in lname:
            return "redemption"
        if "займ" in lname:
            return "lending"
        return "income_other"
    return "other"


class BrokerService:

    def __init__(self, api_token: str, account_id: str) -> None:
        if not api_token or not account_id:
            raise BrokerCredentialsMissingError()
        self._api_token = api_token
        self._account_id = account_id

    async def get_portfolio(self) -> BrokerPortfolio:
        account_id = self._account_id

        async with FinamTradeApiClient(self._api_token) as client:
            account = await client.get(f"/v1/accounts/{account_id}")
            raw_positions: list[dict[str, Any]] = account.get("positions", [])
            symbols = sorted({p["symbol"] for p in raw_positions})

            assets = await asyncio.gather(
                *(client.get(f"/v1/assets/{symbol}", {"account_id": account_id}) for symbol in symbols)
            )
            instruments = dict(zip(symbols, assets))

            transactions_raw = await client.get(
                f"/v1/accounts/{account_id}/transactions",
                {
                    "limit": TRANSACTIONS_LIMIT,
                    "interval.start_time": account["open_account_date"],
                    "interval.end_time": datetime.now(timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z"),
                },
            )

        positions: list[BrokerPosition] = []
        allocation_values: dict[str, Decimal] = {}

        for p in raw_positions:
            quantity = Decimal(str(p["quantity"]["value"]))
            raw_average_price = _money(p.get("average_price"))
            raw_current_price = _money(p.get("current_price"))
            unrealized_pnl = _money(p.get("unrealized_pnl"))
            daily_pnl = _money(p.get("daily_pnl"))

            instrument = instruments.get(p["symbol"], {})
            instrument_type = instrument.get("type")
            asset_class = ASSET_TYPE_LABELS.get(instrument_type, instrument_type or "Прочее")

            bond_details = instrument.get("bond_details")
            if bond_details:
                face_value = _money(bond_details.get("bond_face_value")) or Decimal("1000")
                multiplier = face_value / Decimal("100")
                average_price = raw_average_price * multiplier
                current_price = raw_current_price * multiplier
                average_price_percent = raw_average_price
                current_price_percent = raw_current_price
            else:
                average_price = raw_average_price
                current_price = raw_current_price
                average_price_percent = None
                current_price_percent = None

            market_value = quantity * current_price
            cost_basis = quantity * average_price
            pnl_percent = float(unrealized_pnl / cost_basis * 100) if cost_basis else 0.0

            allocation_values[asset_class] = allocation_values.get(asset_class, Decimal("0")) + market_value

            positions.append(
                BrokerPosition(
                    symbol=p["symbol"],
                    name=instrument.get("name"),
                    asset_class=asset_class,
                    quantity=quantity,
                    average_price=average_price,
                    average_price_percent=average_price_percent,
                    current_price=current_price,
                    current_price_percent=current_price_percent,
                    market_value=market_value,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_percent=pnl_percent,
                    daily_pnl=daily_pnl,
                    weight_percent=0.0,
                )
            )

        total_market_value = sum((pos.market_value for pos in positions), Decimal("0"))
        for pos in positions:
            pos.weight_percent = (
                float(pos.market_value / total_market_value * 100) if total_market_value else 0.0
            )

        allocation = sorted(
            (
                BrokerAllocationItem(
                    asset_class=name,
                    market_value=value,
                    weight_percent=float(value / total_market_value * 100) if total_market_value else 0.0,
                )
                for name, value in allocation_values.items()
            ),
            key=lambda item: item.market_value,
            reverse=True,
        )

        cash = [
            BrokerCashBalance(currency=c["currency_code"], amount=_cash_amount(c))
            for c in account.get("cash", [])
        ]

        daily_pnl_total = sum((pos.daily_pnl for pos in positions), Decimal("0"))
        unrealized_pnl_total = _money(account.get("unrealized_profit"))

        income = self._build_income_breakdown(
            transactions_raw.get("transactions", []), unrealized_pnl_total, account["open_account_date"]
        )
        transactions = self._build_transactions(transactions_raw.get("transactions", []))

        return BrokerPortfolio(
            account_id=account["account_id"],
            status=account.get("status", "UNKNOWN"),
            equity=_money(account.get("equity")),
            unrealized_pnl=unrealized_pnl_total,
            daily_pnl=daily_pnl_total,
            cash=cash,
            positions=sorted(positions, key=lambda pos: pos.market_value, reverse=True),
            allocation=allocation,
            income=income,
            transactions=transactions,
            updated_at=datetime.now(timezone.utc),
        )

    def _build_income_breakdown(
        self,
        raw_transactions: list[dict[str, Any]],
        unrealized_pnl: Decimal,
        period_from: str,
    ) -> BrokerIncomeBreakdown:
        buckets = {
            "coupon": Decimal("0"),
            "dividend": Decimal("0"),
            "redemption": Decimal("0"),
            "lending": Decimal("0"),
            "income_other": Decimal("0"),
            "commission": Decimal("0"),
        }
        for tx in raw_transactions:
            category = tx.get("category", "")
            name = tx.get("transaction_name", "")
            kind = _classify_transaction(category, name)
            if kind not in buckets:
                continue
            change = tx.get("change")
            amount = _cash_amount(change) if change else Decimal("0")
            buckets[kind] += amount

        total_return = unrealized_pnl + sum(buckets.values())

        return BrokerIncomeBreakdown(
            coupon=buckets["coupon"],
            dividend=buckets["dividend"],
            redemption=buckets["redemption"],
            lending=buckets["lending"],
            other=buckets["income_other"],
            commission=buckets["commission"],
            total_return=total_return,
            period_from=_parse_timestamp(period_from),
        )

    def _build_transactions(self, raw_transactions: list[dict[str, Any]]) -> list[BrokerTransaction]:
        result = []
        for tx in raw_transactions[:RECENT_TRANSACTIONS_LIMIT]:
            category = tx.get("category", "")
            name = tx.get("transaction_name", "")
            change = tx.get("change")
            result.append(
                BrokerTransaction(
                    id=tx["id"],
                    timestamp=_parse_timestamp(tx["timestamp"]),
                    kind=_classify_transaction(category, name),
                    name=name,
                    symbol=tx.get("symbol") or None,
                    amount=_cash_amount(change) if change else Decimal("0"),
                    currency=change["currency_code"] if change else "RUB",
                )
            )
        return result
