from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card
from app.models.cashback import CashbackRule
from app.repositories.base import BaseRepository


class CardRepository(BaseRepository[Card]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Card)

    async def list_by_user(self, user_id: UUID) -> list[Card]:
        result = await self.session.execute(
            select(Card).where(Card.user_id == user_id).order_by(Card.name)
        )
        return list(result.scalars().all())

    async def get_by_id_for_user(self, card_id: UUID, user_id: UUID) -> Card | None:
        result = await self.session.execute(
            select(Card).where(Card.id == card_id, Card.user_id == user_id)
        )
        return result.scalar_one_or_none()


class CashbackRuleRepository(BaseRepository[CashbackRule]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CashbackRule)

    async def list_for_card(self, card_id: UUID) -> list[CashbackRule]:
        result = await self.session.execute(
            select(CashbackRule).where(CashbackRule.card_id == card_id)
        )
        return list(result.scalars().all())

    async def find_active_for_category(
        self, user_id: UUID, category_id: UUID, on_date: date
    ) -> list[tuple[CashbackRule, Card]]:
        result = await self.session.execute(
            select(CashbackRule, Card)
            .join(Card, CashbackRule.card_id == Card.id)
            .where(
                Card.user_id == user_id,
                CashbackRule.category_id == category_id,
                CashbackRule.start_date <= on_date,
                CashbackRule.end_date.is_(None) | (CashbackRule.end_date >= on_date),
            )
        )
        return list(result.all())
