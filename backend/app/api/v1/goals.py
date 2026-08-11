from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, DbSession, get_client_ip
from app.core.responses import APIResponse
from app.schemas.goal import GoalCreate, GoalProgressResponse, GoalResponse, GoalUpdate
from app.services.goal import GoalService

router = APIRouter()


def _goal_response(g) -> GoalResponse:
    return GoalResponse(
        id=str(g.id),
        user_id=str(g.user_id),
        name=g.name,
        target_amount=g.target_amount,
        current_amount=g.current_amount,
        deadline=g.deadline,
        linked_account_id=str(g.linked_account_id) if g.linked_account_id else None,
        status=g.status,
        created_at=g.created_at,
        updated_at=g.updated_at,
    )


@router.post("", response_model=APIResponse[GoalResponse])
async def create_goal(
    data: GoalCreate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[GoalResponse]:
    service = GoalService(db)
    goal = await service.create(user, data, ip=ip)
    return APIResponse(data=_goal_response(goal))


@router.get("", response_model=APIResponse[list[GoalResponse]])
async def list_goals(user: CurrentUser, db: DbSession) -> APIResponse[list[GoalResponse]]:
    service = GoalService(db)
    goals = await service.list_by_user_with_sync(user.id)
    return APIResponse(data=[_goal_response(g) for g in goals])


@router.get("/{goal_id}/progress", response_model=APIResponse[GoalProgressResponse])
async def goal_progress(
    goal_id: UUID, user: CurrentUser, db: DbSession
) -> APIResponse[GoalProgressResponse]:
    service = GoalService(db)
    progress = await service.get_progress(user.id, goal_id)
    return APIResponse(data=progress)


@router.patch("/{goal_id}", response_model=APIResponse[GoalResponse])
async def update_goal(
    goal_id: UUID,
    data: GoalUpdate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[GoalResponse]:
    service = GoalService(db)
    goal = await service.update(user.id, goal_id, data, ip=ip)
    return APIResponse(data=_goal_response(goal))


@router.delete("/{goal_id}", response_model=APIResponse[None])
async def delete_goal(
    goal_id: UUID,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[None]:
    service = GoalService(db)
    await service.delete(user.id, goal_id, ip=ip)
    return APIResponse(message="Goal deleted")
