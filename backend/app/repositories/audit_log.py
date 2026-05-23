from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AuditLog)

    async def create_log(
        self,
        action: str,
        entity_type: str,
        user_id: UUID | None = None,
        entity_id: UUID | None = None,
        payload: dict | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            ip_address=ip_address,
        )
        return await self.create(log)
