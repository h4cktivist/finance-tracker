from datetime import date

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.core.responses import APIResponse
from app.schemas.analytics import (
    DashboardResponse,
    HeatmapResponse,
    RatiosResponse,
    StatisticsResponse,
)
from app.services.analytics import AnalyticsService

router = APIRouter()


@router.get("/dashboard", response_model=APIResponse[DashboardResponse])
async def dashboard(user: CurrentUser, db: DbSession) -> APIResponse[DashboardResponse]:
    service = AnalyticsService(db)
    data = await service.dashboard(user.id)
    return APIResponse(data=data)


@router.get("/statistics", response_model=APIResponse[StatisticsResponse])
async def statistics(
    user: CurrentUser, db: DbSession, date_from: date | None = None, date_to: date | None = None
) -> APIResponse[StatisticsResponse]:
    service = AnalyticsService(db)
    data = await service.statistics(user.id, date_from, date_to)
    return APIResponse(data=data)


@router.get("/heatmap", response_model=APIResponse[HeatmapResponse])
async def heatmap(
    user: CurrentUser, db: DbSession, date_from: date | None = None, date_to: date | None = None
) -> APIResponse[HeatmapResponse]:
    service = AnalyticsService(db)
    data = await service.heatmap(user.id, date_from, date_to)
    return APIResponse(data=data)


@router.get("/ratios", response_model=APIResponse[RatiosResponse])
async def ratios(user: CurrentUser, db: DbSession) -> APIResponse[RatiosResponse]:
    service = AnalyticsService(db)
    data = await service.ratios(user.id)
    return APIResponse(data=data)
