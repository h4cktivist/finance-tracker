import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.tasks.celery_app import celery_app

T = TypeVar("T")


def _run_async(coro_factory: Callable[[AsyncSession], Awaitable[T]]) -> T:

    async def _runner() -> T:
        settings = get_settings()
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
        )
        try:
            async with session_factory() as session:
                try:
                    result = await coro_factory(session)
                    await session.commit()
                    return result
                except Exception:
                    await session.rollback()
                    raise
        finally:
            await engine.dispose()

    return asyncio.run(_runner())


@celery_app.task(name="app.tasks.jobs.process_recurring_transactions")
def process_recurring_transactions() -> int:

    async def _job(session: AsyncSession) -> int:
        from app.services.recurring import RecurringService

        service = RecurringService(session)
        return await service.process_due()

    return _run_async(_job)


@celery_app.task(name="app.tasks.jobs.check_budgets")
def check_budgets() -> None:

    async def _job(session: AsyncSession) -> None:
        from app.services.budget import BudgetService

        service = BudgetService(session)
        await service.check_all_budgets()

    _run_async(_job)


@celery_app.task(name="app.tasks.jobs.check_goal_deadlines")
def check_goal_deadlines() -> None:

    async def _job(session: AsyncSession) -> None:
        from app.services.goal import GoalService

        service = GoalService(session)
        await service.check_deadlines()

    _run_async(_job)
