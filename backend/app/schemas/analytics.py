from decimal import Decimal

from pydantic import BaseModel


class DashboardResponse(BaseModel):
    total_balance: Decimal
    total_income: Decimal
    total_expenses: Decimal
    savings_rate: float
    cashback_earned: Decimal
    goals_progress: list[dict]


class CategoryStat(BaseModel):
    category_id: str
    category_name: str
    total: Decimal


class StatisticsResponse(BaseModel):
    top_expense_categories: list[CategoryStat]
    top_income_categories: list[CategoryStat]
    cashflow: Decimal
    average_daily_spending: Decimal
    average_monthly_income: Decimal


class HeatmapDay(BaseModel):
    date: str
    count: int
    intensity: float
    total_amount: Decimal


class HeatmapResponse(BaseModel):
    days: list[HeatmapDay]


class RatiosResponse(BaseModel):
    savings_rate: float
    expense_to_income_ratio: float
    discretionary_spending_ratio: float
