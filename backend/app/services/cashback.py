from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.card import Card
from app.models.cashback import CashbackAccrual, CashbackAccrualStatus, CashbackRule
from app.models.transaction import Transaction, TransactionType
from app.repositories.account import AccountRepository
from app.repositories.card import CardRepository, CashbackRuleRepository
from app.repositories.cashback import CashbackAccrualRepository
from app.repositories.category import CategoryRepository
from app.schemas.cashback import CardCreate, CashbackRecommendation, CashbackRuleCreate
from app.services.audit import AuditService
from app.services.notification import NotificationService


class CashbackService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.card_repo = CardRepository(session)
        self.account_repo = AccountRepository(session)
        self.category_repo = CategoryRepository(session)
        self.rule_repo = CashbackRuleRepository(session)
        self.accrual_repo = CashbackAccrualRepository(session)
        self.audit = AuditService(session)
        self.notifications = NotificationService(session)

    async def create_card(self, user_id: UUID, data: CardCreate, ip: str | None = None) -> Card:
        account = await self.account_repo.get_by_id_for_user(UUID(data.account_id), user_id)
        if account is None:
            raise NotFoundError("Account not found")
        card = Card(
            user_id=user_id,
            account_id=account.id,
            name=data.name,
            bank_name=data.bank_name,
            last_digits=data.last_digits,
        )
        await self.card_repo.create(card)
        await self.audit.log("create", "card", user_id=user_id, entity_id=card.id, ip_address=ip)
        return card

    async def create_rule(
        self, user_id: UUID, card_id: UUID, data: CashbackRuleCreate, ip: str | None = None
    ) -> CashbackRule:
        card = await self.card_repo.get_by_id_for_user(card_id, user_id)
        if card is None:
            raise NotFoundError("Card not found")
        category = await self.category_repo.get_by_id_for_user(UUID(data.category_id), user_id)
        if category is None:
            raise NotFoundError("Category not found")
        rule = CashbackRule(
            card_id=card.id,
            category_id=category.id,
            cashback_percent=data.cashback_percent,
            monthly_limit=data.monthly_limit,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        await self.rule_repo.create(rule)
        await self.audit.log(
            "create", "cashback_rule", user_id=user_id, entity_id=rule.id, ip_address=ip
        )
        return rule

    async def evaluate(
        self, user_id: UUID, transaction: Transaction, category_id: UUID, card_id: str | None
    ) -> CashbackAccrual | None:
        if transaction.type != TransactionType.EXPENSE:
            return None
        period_month = transaction.transaction_date.strftime("%Y-%m")
        rules = await self.rule_repo.find_active_for_category(
            user_id, category_id, transaction.transaction_date
        )
        if not rules:
            return None
        if card_id:
            rules = [(rule, card) for (rule, card) in rules if str(card.id) == card_id]
            if not rules:
                return None
        best: tuple[CashbackRule, Card, Decimal] | None = None
        seen_missed_cards: set[UUID] = set()
        for rule, card in rules:
            potential = transaction.amount * rule.cashback_percent / Decimal("100")
            monthly_used = await self.accrual_repo.monthly_total_for_card_category(
                card.id, category_id, period_month
            )
            if rule.monthly_limit and monthly_used + potential > rule.monthly_limit:
                remaining = rule.monthly_limit - monthly_used
                if remaining <= 0:
                    if card.id not in seen_missed_cards:
                        await self._record_missed(user_id, transaction, card, rule, period_month)
                        seen_missed_cards.add(card.id)
                    continue
                potential = remaining
            if best is None or potential > best[2]:
                best = (rule, card, potential)
        if best is None:
            return None
        rule, card, amount = best
        accrual = CashbackAccrual(
            user_id=user_id,
            transaction_id=transaction.id,
            card_id=card.id,
            rule_id=rule.id,
            amount=amount,
            period_month=period_month,
            status=CashbackAccrualStatus.ACCRUED,
        )
        await self.accrual_repo.create(accrual)
        await self.notifications.notify_cashback_available(user_id, accrual, card)
        return accrual

    async def _record_missed(
        self,
        user_id: UUID,
        transaction: Transaction,
        card: Card,
        rule: CashbackRule,
        period_month: str,
    ) -> None:
        existing = await self.session.execute(
            select(CashbackAccrual.id).where(
                CashbackAccrual.transaction_id == transaction.id, CashbackAccrual.card_id == card.id
            )
        )
        if existing.scalar_one_or_none() is not None:
            return
        missed_amount = transaction.amount * rule.cashback_percent / Decimal("100")
        accrual = CashbackAccrual(
            user_id=user_id,
            transaction_id=transaction.id,
            card_id=card.id,
            rule_id=rule.id,
            amount=missed_amount,
            period_month=period_month,
            status=CashbackAccrualStatus.MISSED,
        )
        await self.accrual_repo.create(accrual)

    async def get_recommendations(
        self, user_id: UUID, category_id: UUID
    ) -> list[CashbackRecommendation]:
        rules = await self.rule_repo.find_active_for_category(user_id, category_id, date.today())
        if not rules:
            return []
        best_rule, best_card = max(rules, key=lambda r: r[0].cashback_percent)
        return [
            CashbackRecommendation(
                category_id=str(category_id),
                best_card_id=str(best_card.id),
                best_card_name=best_card.name,
                cashback_percent=best_rule.cashback_percent,
            )
        ]
