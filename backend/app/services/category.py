from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.category import Category
from app.models.user import User
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryTreeNode, CategoryUpdate
from app.services.audit import AuditService


class CategoryService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CategoryRepository(session)
        self.audit = AuditService(session)

    async def create(self, user: User, data: CategoryCreate, ip: str | None = None) -> Category:
        parent_id = UUID(data.parent_category_id) if data.parent_category_id else None
        if parent_id:
            parent = await self.repo.get_by_id_for_user(parent_id, user.id)
            if parent is None:
                raise NotFoundError("Parent category not found")
            if parent.type != data.type:
                raise ValidationError("Parent category type must match")
        category = Category(
            user_id=user.id,
            name=data.name,
            type=data.type,
            parent_category_id=parent_id,
            color=data.color,
            icon=data.icon,
            is_essential=data.is_essential,
        )
        await self.repo.create(category)
        await self.audit.log(
            "create", "category", user_id=user.id, entity_id=category.id, ip_address=ip
        )
        return category

    async def list(self, user_id: UUID) -> list[Category]:
        return await self.repo.list_by_user(user_id)

    async def get_tree(self, user_id: UUID) -> list[CategoryTreeNode]:
        categories = await self.repo.list_by_user(user_id)
        nodes: dict[str, CategoryTreeNode] = {}
        roots: list[CategoryTreeNode] = []
        for cat in categories:
            node = CategoryTreeNode(
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
                children=[],
            )
            nodes[str(cat.id)] = node
        for cat in categories:
            node = nodes[str(cat.id)]
            if cat.parent_category_id and str(cat.parent_category_id) in nodes:
                nodes[str(cat.parent_category_id)].children.append(node)
            else:
                roots.append(node)
        return roots

    async def update(
        self, user_id: UUID, category_id: UUID, data: CategoryUpdate, ip: str | None = None
    ) -> Category:
        category = await self.repo.get_by_id_for_user(category_id, user_id)
        if category is None:
            raise NotFoundError("Category not found")
        if data.name is not None:
            category.name = data.name
        if data.color is not None:
            category.color = data.color
        if data.icon is not None:
            category.icon = data.icon
        if data.is_essential is not None:
            category.is_essential = data.is_essential
        if data.parent_category_id is not None:
            category.parent_category_id = UUID(data.parent_category_id)
        await self.session.flush()
        await self.audit.log(
            "update", "category", user_id=user_id, entity_id=category.id, ip_address=ip
        )
        return category

    async def delete(self, user_id: UUID, category_id: UUID, ip: str | None = None) -> None:
        category = await self.repo.get_by_id_for_user(category_id, user_id)
        if category is None:
            raise NotFoundError("Category not found")
        await self.repo.soft_delete(category)
        await self.audit.log(
            "delete", "category", user_id=user_id, entity_id=category.id, ip_address=ip
        )
