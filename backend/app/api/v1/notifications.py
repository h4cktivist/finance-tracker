from uuid import UUID

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.core.responses import APIResponse
from app.schemas.notification import NotificationListResponse, NotificationResponse
from app.services.notification import NotificationService

router = APIRouter()


@router.get("", response_model=APIResponse[NotificationListResponse])
async def list_notifications(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
) -> APIResponse[NotificationListResponse]:
    service = NotificationService(db)
    items, total = await service.list(user.id, page, page_size, unread_only)
    pages = (total + page_size - 1) // page_size if page_size else 0
    return APIResponse(
        data=NotificationListResponse(
            items=[
                NotificationResponse(
                    id=str(n.id),
                    type=n.type,
                    title=n.title,
                    body=n.body,
                    payload=n.payload,
                    read_at=n.read_at,
                    created_at=n.created_at,
                )
                for n in items
            ],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
    )


@router.patch("/{notification_id}/read", response_model=APIResponse[NotificationResponse])
async def mark_read(
    notification_id: UUID, user: CurrentUser, db: DbSession
) -> APIResponse[NotificationResponse]:
    service = NotificationService(db)
    n = await service.mark_read(user.id, notification_id)
    return APIResponse(
        data=NotificationResponse(
            id=str(n.id),
            type=n.type,
            title=n.title,
            body=n.body,
            payload=n.payload,
            read_at=n.read_at,
            created_at=n.created_at,
        )
    )


@router.post("/read-all", response_model=APIResponse[dict])
async def mark_all_read(user: CurrentUser, db: DbSession) -> APIResponse[dict]:
    service = NotificationService(db)
    count = await service.mark_all_read(user.id)
    return APIResponse(data={"marked_read": count})
