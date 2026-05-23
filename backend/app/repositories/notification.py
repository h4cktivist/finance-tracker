from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Notification)

    async def list_by_user(
        self, user_id: UUID, *, page: int = 1, page_size: int = 20, unread_only: bool = False
    ) -> tuple[list[Notification], int]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.read_at.is_(None))
        stmt = stmt.order_by(Notification.created_at.desc())
        count_result = await self.session.execute(select(func.count()).select_from(stmt.subquery()))
        total = count_result.scalar_one()
        offset = (page - 1) * page_size
        result = await self.session.execute(stmt.offset(offset).limit(page_size))
        return (list(result.scalars().all()), total)

    async def get_by_id_for_user(self, notification_id: UUID, user_id: UUID) -> Notification | None:
        result = await self.session.execute(
            select(Notification).where(
                Notification.id == notification_id, Notification.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def mark_read(self, notification: Notification) -> Notification:
        notification.read_at = datetime.now(UTC)
        await self.session.flush()
        return notification

    async def mark_all_read(self, user_id: UUID) -> int:
        result = await self.session.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
            .values(read_at=datetime.now(UTC))
        )
        return result.rowcount  # type: ignore[attr-defined]
