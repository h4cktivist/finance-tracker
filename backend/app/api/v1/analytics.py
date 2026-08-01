from datetime import date

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.core.responses import APIResponse
from app.schemas.analytics import (
    DashboardResponse,
    ForecastResponse,
    HeatmapResponse,
    MerchantsResponse,
    RatiosResponse,
    StatisticsResponse,
    TrendsResponse,
)
from app.services.analytics import AnalyticsService
from app.services.forecast import ForecastService

router = APIRouter()


@router.get("/dashboard", response_model=APIResponse[DashboardResponse])
async def dashboard(
    user: CurrentUser,
    db: DbSession,
    exclude_investments: bool = Query(False),
) -> APIResponse[DashboardResponse]:
    service = AnalyticsService(db)
    data = await service.dashboard(user.id, exclude_investments=exclude_investments)
    return APIResponse(data=data)


@router.get("/statistics", response_model=APIResponse[StatisticsResponse])
async def statistics(
    user: CurrentUser,
    db: DbSession,
    date_from: date | None = None,
    date_to: date | None = None,
    exclude_investments: bool = Query(False),
) -> APIResponse[StatisticsResponse]:
    service = AnalyticsService(db)
    data = await service.statistics(
        user.id, date_from, date_to, exclude_investments=exclude_investments
    )
    return APIResponse(data=data)


@router.get("/merchants", response_model=APIResponse[MerchantsResponse])
async def merchants(
    user: CurrentUser,
    db: DbSession,
    date_from: date | None = None,
    date_to: date | None = None,
    exclude_investments: bool = Query(False),
) -> APIResponse[MerchantsResponse]:
    service = AnalyticsService(db)
    data = await service.merchants(
        user.id, date_from, date_to, exclude_investments=exclude_investments
    )
    return APIResponse(data=data)


@router.get("/heatmap", response_model=APIResponse[HeatmapResponse])
async def heatmap(
    user: CurrentUser,
    db: DbSession,
    date_from: date | None = None,
    date_to: date | None = None,
    exclude_investments: bool = Query(False),
) -> APIResponse[HeatmapResponse]:
    service = AnalyticsService(db)
    data = await service.heatmap(
        user.id, date_from, date_to, exclude_investments=exclude_investments
    )
    return APIResponse(data=data)


@router.get("/ratios", response_model=APIResponse[RatiosResponse])
async def ratios(
    user: CurrentUser,
    db: DbSession,
    exclude_investments: bool = Query(False),
    date_from: date | None = None,
    date_to: date | None = None,
) -> APIResponse[RatiosResponse]:
    service = AnalyticsService(db)
    data = await service.ratios(
        user.id,
        date_from=date_from,
        date_to=date_to,
        exclude_investments=exclude_investments,
    )
    return APIResponse(data=data)


@router.get("/trends", response_model=APIResponse[TrendsResponse])
async def trends(
    user: CurrentUser,
    db: DbSession,
    date_from: date | None = None,
    date_to: date | None = None,
    exclude_investments: bool = Query(False),
) -> APIResponse[TrendsResponse]:
    service = AnalyticsService(db)
    data = await service.trends(
        user.id, date_from, date_to, exclude_investments=exclude_investments
    )
    return APIResponse(data=data)


@router.get("/forecast", response_model=APIResponse[ForecastResponse])
async def forecast(
    user: CurrentUser,
    db: DbSession,
    month: str | None = Query(None, description="Целевой месяц YYYY-MM (по умолчанию — следующий)"),
    exclude_investments: bool = Query(False),
) -> APIResponse[ForecastResponse]:
    service = ForecastService(db)
    data = await service.forecast(
        user.id, month=month, exclude_investments=exclude_investments
    )
    return APIResponse(data=data)
