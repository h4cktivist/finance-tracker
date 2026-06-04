from calendar import monthrange
from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recurring import RecurringTransaction
from app.models.transaction import TransactionType
from app.repositories.recurring import RecurringRepository
from app.schemas.analytics import ForecastBreakdown, ForecastResponse
from app.services.analytics import AnalyticsService
from app.services.recurring import advance_date

Confidence = Literal["low", "medium", "high"]
HISTORY_MONTHS = 3
MAX_ADVANCE_ITERATIONS = 500


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    return start, date(year, month, last_day)


def _parse_target_month(month: str | None) -> tuple[int, int]:
    if month is None:
        today = date.today()
        if today.month == 12:
            return today.year + 1, 1
        return today.year, today.month + 1
    parts = month.strip().split("-")
    if len(parts) != 2:
        raise ValueError("month должен быть в формате YYYY-MM")
    year, mon = int(parts[0]), int(parts[1])
    if not (1 <= mon <= 12):
        raise ValueError("Некорректный месяц")
    return year, mon


def _months_before(year: int, month: int, count: int) -> list[tuple[int, int]]:
    y, m = year, month
    result: list[tuple[int, int]] = []
    for _ in range(count):
        m -= 1
        if m < 1:
            m = 12
            y -= 1
        result.append((y, m))
    result.reverse()
    return result


def _execution_count_in_period(
    recurring: RecurringTransaction,
    period_start: date,
    period_end: date,
    *,
    anchor: date,
    require_active: bool,
) -> int:
    if recurring.type == TransactionType.TRANSFER:
        return 0
    if require_active and not recurring.is_active:
        return 0
    if recurring.end_date and recurring.end_date < period_start:
        return 0
    if recurring.start_date > period_end:
        return 0

    current = max(anchor, recurring.start_date)
    iterations = 0
    while current < period_start and iterations < MAX_ADVANCE_ITERATIONS:
        if recurring.end_date and current > recurring.end_date:
            return 0
        current = advance_date(current, recurring.frequency, recurring.interval)
        iterations += 1

    count = 0
    while current <= period_end and iterations < MAX_ADVANCE_ITERATIONS:
        if recurring.end_date and current > recurring.end_date:
            break
        if current >= recurring.start_date and current >= period_start:
            count += 1
        current = advance_date(current, recurring.frequency, recurring.interval)
        iterations += 1
    return count


def _recurring_totals_for_period(
    recurring_list: list[RecurringTransaction],
    period_start: date,
    period_end: date,
    investment_category_ids: set[UUID],
    *,
    for_future: bool,
) -> tuple[Decimal, Decimal]:
    income = Decimal("0")
    expenses = Decimal("0")
    for item in recurring_list:
        if (
            item.type == TransactionType.EXPENSE
            and item.category_id
            and item.category_id in investment_category_ids
        ):
            continue
        anchor = item.next_execution_date if for_future else item.start_date
        count = _execution_count_in_period(
            item,
            period_start,
            period_end,
            anchor=anchor,
            require_active=for_future,
        )
        if count == 0:
            continue
        total = item.amount * count
        if item.type == TransactionType.INCOME:
            income += total
        elif item.type == TransactionType.EXPENSE:
            expenses += total
    return income, expenses


class ForecastService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.analytics = AnalyticsService(session)
        self.recurring_repo = RecurringRepository(session)

    async def forecast(
        self,
        user_id: UUID,
        *,
        month: str | None = None,
        exclude_investments: bool = False,
    ) -> ForecastResponse:
        try:
            target_year, target_month = _parse_target_month(month)
        except ValueError as exc:
            from app.core.exceptions import ValidationError

            raise ValidationError(str(exc)) from exc

        target_start, target_end = _month_bounds(target_year, target_month)
        if target_start <= date.today():
            from app.core.exceptions import ValidationError

            raise ValidationError("Прогноз доступен только для будущих месяцев")

        investment_ids: list[UUID] = []
        if exclude_investments:
            investment_ids = await self.analytics._investment_expense_category_ids(user_id)
        investment_set = set(investment_ids)

        recurring_list = await self.recurring_repo.list_by_user(user_id)
        recurring_income, recurring_expenses = _recurring_totals_for_period(
            recurring_list,
            target_start,
            target_end,
            investment_set,
            for_future=True,
        )

        history_months = _months_before(target_year, target_month, HISTORY_MONTHS)
        monthly_income: list[Decimal] = []
        monthly_expenses: list[Decimal] = []
        monthly_recurring_income: list[Decimal] = []
        monthly_recurring_expenses: list[Decimal] = []

        for y, m in history_months:
            m_start, m_end = _month_bounds(y, m)
            inc, exp = await self.analytics._sum_income_expenses(
                user_id, m_start, m_end, investment_ids or None
            )
            r_inc, r_exp = _recurring_totals_for_period(
                recurring_list,
                m_start,
                m_end,
                investment_set,
                for_future=False,
            )
            monthly_income.append(inc)
            monthly_expenses.append(exp)
            monthly_recurring_income.append(r_inc)
            monthly_recurring_expenses.append(r_exp)

        months_used = len(history_months)
        if months_used == 0:
            trend_income = Decimal("0")
            trend_expenses = Decimal("0")
        else:
            variable_income = [
                max(Decimal("0"), monthly_income[i] - monthly_recurring_income[i])
                for i in range(months_used)
            ]
            variable_expenses = [
                max(Decimal("0"), monthly_expenses[i] - monthly_recurring_expenses[i])
                for i in range(months_used)
            ]
            trend_income = sum(variable_income, Decimal("0")) / months_used
            trend_expenses = sum(variable_expenses, Decimal("0")) / months_used

        income = recurring_income + trend_income
        expenses = recurring_expenses + trend_expenses
        cashflow = income - expenses

        months_with_data = sum(
            1 for i in range(months_used) if monthly_income[i] > 0 or monthly_expenses[i] > 0
        )
        if months_with_data >= HISTORY_MONTHS:
            confidence: Confidence = "high"
        elif months_with_data >= 1:
            confidence = "medium"
        else:
            confidence = "low"

        return ForecastResponse(
            target_month=f"{target_year:04d}-{target_month:02d}",
            income=income,
            expenses=expenses,
            cashflow=cashflow,
            income_breakdown=ForecastBreakdown(recurring=recurring_income, trend=trend_income),
            expenses_breakdown=ForecastBreakdown(
                recurring=recurring_expenses, trend=trend_expenses
            ),
            confidence=confidence,
            months_used=months_used,
        )
