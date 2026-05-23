from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, DbSession, get_client_ip
from app.core.responses import APIResponse
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryTreeNode, CategoryUpdate
from app.services.category import CategoryService

router = APIRouter()


def _cat_response(cat) -> CategoryResponse:
    return CategoryResponse(
        id=str(cat.id),
        user_id=str(cat.user_id),
        name=cat.name,
        type=cat.type,
        parent_category_id=str(cat.parent_category_id) if cat.parent_category_id else None,
        color=cat.color,
        icon=cat.icon,
        is_essential=cat.is_essential,
        created_at=cat.created_at,
        updated_at=cat.updated_at,
    )


@router.post("", response_model=APIResponse[CategoryResponse])
async def create_category(
    data: CategoryCreate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[CategoryResponse]:
    service = CategoryService(db)
    cat = await service.create(user, data, ip=ip)
    return APIResponse(data=_cat_response(cat))


@router.get("", response_model=APIResponse[list[CategoryResponse]])
async def list_categories(user: CurrentUser, db: DbSession) -> APIResponse[list[CategoryResponse]]:
    service = CategoryService(db)
    cats = await service.list(user.id)
    return APIResponse(data=[_cat_response(c) for c in cats])


@router.get("/tree", response_model=APIResponse[list[CategoryTreeNode]])
async def category_tree(user: CurrentUser, db: DbSession) -> APIResponse[list[CategoryTreeNode]]:
    service = CategoryService(db)
    tree = await service.get_tree(user.id)
    return APIResponse(data=tree)


@router.patch("/{category_id}", response_model=APIResponse[CategoryResponse])
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[CategoryResponse]:
    service = CategoryService(db)
    cat = await service.update(user.id, category_id, data, ip=ip)
    return APIResponse(data=_cat_response(cat))


@router.delete("/{category_id}", response_model=APIResponse[None])
async def delete_category(
    category_id: UUID,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[None]:
    service = CategoryService(db)
    await service.delete(user.id, category_id, ip=ip)
    return APIResponse(message="Category deleted")
