from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category, CategoryType
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Category)

    async def list_by_user(self, user_id: UUID) -> list[Category]:
        result = await self.session.execute(
            select(Category)
            .where(Category.user_id == user_id, Category.deleted_at.is_(None))
            .order_by(Category.name)
        )
        return list(result.scalars().all())

    async def get_by_id_for_user(self, category_id: UUID, user_id: UUID) -> Category | None:
        result = await self.session.execute(
            select(Category).where(
                Category.id == category_id,
                Category.user_id == user_id,
                Category.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def find_by_name(
        self, user_id: UUID, name: str, category_type: CategoryType
    ) -> Category | None:
        result = await self.session.execute(
            select(Category)
            .where(
                Category.user_id == user_id,
                Category.type == category_type,
                func.lower(Category.name) == name.lower(),
                Category.deleted_at.is_(None),
            )
            .order_by(Category.created_at)
            .limit(1)
        )
        return result.scalar_one_or_none()
