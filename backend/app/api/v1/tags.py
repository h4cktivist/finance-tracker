from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, DbSession, get_client_ip
from app.core.responses import APIResponse
from app.schemas.tag import TagCreate, TagResponse, TagUpdate
from app.services.tag import TagService

router = APIRouter()


def _tag_response(tag) -> TagResponse:
    return TagResponse(
        id=str(tag.id),
        user_id=str(tag.user_id),
        name=tag.name,
        color=tag.color,
        created_at=tag.created_at,
        updated_at=tag.updated_at,
    )


@router.post("", response_model=APIResponse[TagResponse])
async def create_tag(
    data: TagCreate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[TagResponse]:
    service = TagService(db)
    tag = await service.create(user, data, ip=ip)
    return APIResponse(data=_tag_response(tag))


@router.get("", response_model=APIResponse[list[TagResponse]])
async def list_tags(user: CurrentUser, db: DbSession) -> APIResponse[list[TagResponse]]:
    service = TagService(db)
    tags = await service.list(user.id)
    return APIResponse(data=[_tag_response(t) for t in tags])


@router.patch("/{tag_id}", response_model=APIResponse[TagResponse])
async def update_tag(
    tag_id: UUID,
    data: TagUpdate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[TagResponse]:
    service = TagService(db)
    tag = await service.update(user.id, tag_id, data, ip=ip)
    return APIResponse(data=_tag_response(tag))


@router.delete("/{tag_id}", response_model=APIResponse[None])
async def delete_tag(
    tag_id: UUID,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[None]:
    service = TagService(db)
    await service.delete(user.id, tag_id, ip=ip)
    return APIResponse(message="Tag deleted")
