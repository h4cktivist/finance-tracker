from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, DbSession, get_client_ip
from app.core.responses import APIResponse
from app.repositories.budget import BudgetRepository
from app.schemas.budget import BudgetCreate, BudgetResponse, BudgetStatusResponse, BudgetUpdate
from app.services.budget import BudgetService

router = APIRouter()


def _budget_response(b) -> BudgetResponse:
    return BudgetResponse(
        id=str(b.id),
        user_id=str(b.user_id),
        category_id=str(b.category_id),
        amount_limit=b.amount_limit,
        period_type=b.period_type,
        start_date=b.start_date,
        end_date=b.end_date,
        rollover_enabled=b.rollover_enabled,
        created_at=b.created_at,
        updated_at=b.updated_at,
    )


@router.post("", response_model=APIResponse[BudgetResponse])
async def create_budget(
    data: BudgetCreate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[BudgetResponse]:
    service = BudgetService(db)
    budget = await service.create(user, data, ip=ip)
    return APIResponse(data=_budget_response(budget))


@router.get("", response_model=APIResponse[list[BudgetResponse]])
async def list_budgets(user: CurrentUser, db: DbSession) -> APIResponse[list[BudgetResponse]]:
    repo = BudgetRepository(db)
    budgets = await repo.list_by_user(user.id)
    return APIResponse(data=[_budget_response(b) for b in budgets])


@router.get("/{budget_id}/status", response_model=APIResponse[BudgetStatusResponse])
async def budget_status(
    budget_id: UUID, user: CurrentUser, db: DbSession
) -> APIResponse[BudgetStatusResponse]:
    service = BudgetService(db)
    status = await service.get_status(user.id, budget_id)
    return APIResponse(data=status)


@router.patch("/{budget_id}", response_model=APIResponse[BudgetResponse])
async def update_budget(
    budget_id: UUID,
    data: BudgetUpdate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[BudgetResponse]:
    service = BudgetService(db)
    budget = await service.update(user.id, budget_id, data, ip=ip)
    return APIResponse(data=_budget_response(budget))


@router.delete("/{budget_id}", response_model=APIResponse[None])
async def delete_budget(
    budget_id: UUID,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[None]:
    service = BudgetService(db)
    await service.delete(user.id, budget_id, ip=ip)
    return APIResponse(message="Budget deleted")
