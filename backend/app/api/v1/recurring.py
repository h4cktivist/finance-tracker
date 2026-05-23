from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, DbSession, get_client_ip
from app.core.responses import APIResponse
from app.repositories.recurring import RecurringRepository
from app.schemas.recurring import RecurringCreate, RecurringResponse, RecurringUpdate
from app.services.recurring import RecurringService

router = APIRouter()


def _recurring_response(r) -> RecurringResponse:
    return RecurringResponse(
        id=str(r.id),
        user_id=str(r.user_id),
        frequency=r.frequency,
        interval=r.interval,
        start_date=r.start_date,
        end_date=r.end_date,
        next_execution_date=r.next_execution_date,
        is_active=r.is_active,
        account_id=str(r.account_id),
        category_id=str(r.category_id) if r.category_id else None,
        type=r.type,
        amount=r.amount,
        description=r.description,
        created_at=r.created_at,
    )


@router.post("", response_model=APIResponse[RecurringResponse])
async def create_recurring(
    data: RecurringCreate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[RecurringResponse]:
    service = RecurringService(db)
    recurring = await service.create(user, data, ip=ip)
    return APIResponse(data=_recurring_response(recurring))


@router.get("", response_model=APIResponse[list[RecurringResponse]])
async def list_recurring(user: CurrentUser, db: DbSession) -> APIResponse[list[RecurringResponse]]:
    repo = RecurringRepository(db)
    items = await repo.list_by_user(user.id)
    return APIResponse(data=[_recurring_response(r) for r in items])


@router.patch("/{recurring_id}", response_model=APIResponse[RecurringResponse])
async def update_recurring(
    recurring_id: UUID,
    data: RecurringUpdate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[RecurringResponse]:
    service = RecurringService(db)
    recurring = await service.update(user.id, recurring_id, data, ip=ip)
    return APIResponse(data=_recurring_response(recurring))
