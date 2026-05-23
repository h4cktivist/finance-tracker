from datetime import date

from app.models.recurring import RecurringFrequency
from app.services.recurring import advance_date


def test_advance_daily():
    result = advance_date(date(2026, 1, 1), RecurringFrequency.DAILY, 2)
    assert result == date(2026, 1, 3)


def test_advance_weekly():
    result = advance_date(date(2026, 1, 1), RecurringFrequency.WEEKLY, 1)
    assert result == date(2026, 1, 8)


def test_advance_monthly():
    result = advance_date(date(2026, 1, 15), RecurringFrequency.MONTHLY, 1)
    assert result == date(2026, 2, 15)


def test_advance_yearly():
    result = advance_date(date(2026, 5, 23), RecurringFrequency.YEARLY, 1)
    assert result == date(2027, 5, 23)
