from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit_log import AuditLogRepository


class AuditService:

    def __init__(self, session: AsyncSession) -> None:
        self.repo = AuditLogRepository(session)

    async def log(
        self,
        action: str,
        entity_type: str,
        *,
        user_id: UUID | None = None,
        entity_id: UUID | None = None,
        payload: dict | None = None,
        ip_address: str | None = None,
    ) -> None:
        await self.repo.create_log(
            action=action,
            entity_type=entity_type,
            user_id=user_id,
            entity_id=entity_id,
            payload=payload,
            ip_address=ip_address,
        )
