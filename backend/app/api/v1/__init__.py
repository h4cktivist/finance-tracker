from fastapi import APIRouter

from app.api.v1 import (
    accounts,
    ai,
    analytics,
    auth,
    broker,
    budgets,
    cashback,
    categories,
    goals,
    notifications,
    recurring,
    tags,
    transactions,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(broker.router, prefix="/broker", tags=["broker"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(budgets.router, prefix="/budgets", tags=["budgets"])
api_router.include_router(recurring.router, prefix="/recurring", tags=["recurring"])
api_router.include_router(cashback.router, prefix="/cashback", tags=["cashback"])
api_router.include_router(goals.router, prefix="/goals", tags=["goals"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
