from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.tag import Tag
from app.models.user import User
from app.repositories.tag import TagRepository
from app.schemas.tag import TagCreate, TagUpdate
from app.services.audit import AuditService


class TagService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TagRepository(session)
        self.audit = AuditService(session)

    async def create(self, user: User, data: TagCreate, ip: str | None = None) -> Tag:
        existing = await self.session.execute(
            select(Tag.id).where(
                Tag.user_id == user.id, Tag.name == data.name, Tag.deleted_at.is_(None)
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictError("Tag name already exists")
        tag = Tag(user_id=user.id, name=data.name, color=data.color)
        try:
            await self.repo.create(tag)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Tag name already exists") from exc
        await self.audit.log("create", "tag", user_id=user.id, entity_id=tag.id, ip_address=ip)
        return tag

    async def list(self, user_id: UUID) -> list[Tag]:
        return await self.repo.list_by_user(user_id)

    async def update(
        self, user_id: UUID, tag_id: UUID, data: TagUpdate, ip: str | None = None
    ) -> Tag:
        tag = await self.repo.get_by_id_for_user(tag_id, user_id)
        if tag is None:
            raise NotFoundError("Tag not found")
        if data.name is not None:
            tag.name = data.name
        if data.color is not None:
            tag.color = data.color
        await self.session.flush()
        await self.audit.log("update", "tag", user_id=user_id, entity_id=tag.id, ip_address=ip)
        return tag

    async def delete(self, user_id: UUID, tag_id: UUID, ip: str | None = None) -> None:
        tag = await self.repo.get_by_id_for_user(tag_id, user_id)
        if tag is None:
            raise NotFoundError("Tag not found")
        await self.repo.soft_delete(tag)
        await self.audit.log("delete", "tag", user_id=user_id, entity_id=tag.id, ip_address=ip)
