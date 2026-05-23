from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery(
    "finance_tracker", broker=settings.celery_broker_url, backend=settings.celery_result_backend
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "process-recurring-transactions": {
            "task": "app.tasks.jobs.process_recurring_transactions",
            "schedule": crontab(hour=0, minute=5),
        },
        "check-budgets": {
            "task": "app.tasks.jobs.check_budgets",
            "schedule": crontab(hour=8, minute=0),
        },
        "check-goal-deadlines": {
            "task": "app.tasks.jobs.check_goal_deadlines",
            "schedule": crontab(hour=9, minute=0),
        },
    },
)
celery_app.autodiscover_tasks(["app.tasks"])
