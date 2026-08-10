from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.card import Card
from app.models.cashback import (
    CashbackAccrual,
    CashbackAccrualStatus,
    CashbackPayout,
    CashbackRule,
)
from app.models.category import Category, CategoryType
from app.models.transaction import Transaction, TransactionType
from app.repositories.account import AccountRepository
from app.repositories.card import CardRepository, CashbackRuleRepository
from app.repositories.cashback import CashbackAccrualRepository, CashbackPayoutRepository
from app.repositories.category import CategoryRepository
from app.repositories.transaction import TransactionRepository
from app.schemas.cashback import (
    CardCreate,
    CashbackPayoutCardPreview,
    CashbackPayoutCreate,
    CashbackPayoutPreview,
    CashbackRecommendation,
    CashbackRuleCreate,
    CashbackRuleUpdate,
)
from app.schemas.transaction import TransactionCreate
from app.services.audit import AuditService
from app.services.notification import NotificationService

CASHBACK_CATEGORY_NAME = "Кэшбэк"

_MONTH_NAMES_GENITIVE = (
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)


def previous_period_month(today: date | None = None) -> str:
    """Прошлый месяц в формате `YYYY-MM`."""
    ref = today or date.today()
    year, month = (ref.year - 1, 12) if ref.month == 1 else (ref.year, ref.month - 1)
    return f"{year}-{month:02d}"


class CashbackService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.card_repo = CardRepository(session)
        self.account_repo = AccountRepository(session)
        self.category_repo = CategoryRepository(session)
        self.rule_repo = CashbackRuleRepository(session)
        self.accrual_repo = CashbackAccrualRepository(session)
        self.payout_repo = CashbackPayoutRepository(session)
        self.tx_repo = TransactionRepository(session)
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
            min_purchase_amount=data.min_purchase_amount,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        await self.rule_repo.create(rule)
        await self.audit.log(
            "create", "cashback_rule", user_id=user_id, entity_id=rule.id, ip_address=ip
        )
        return rule

    async def update_rule(
        self,
        user_id: UUID,
        card_id: UUID,
        rule_id: UUID,
        data: CashbackRuleUpdate,
        ip: str | None = None,
    ) -> tuple[CashbackRule, int]:
        card = await self.card_repo.get_by_id_for_user(card_id, user_id)
        if card is None:
            raise NotFoundError("Card not found")
        rule = await self.rule_repo.get_by_id_for_card(rule_id, card_id)
        if rule is None:
            raise NotFoundError("Cashback rule not found")
        fields_set = data.model_fields_set
        if "cashback_percent" in fields_set and data.cashback_percent is not None:
            rule.cashback_percent = data.cashback_percent
        if "monthly_limit" in fields_set:
            rule.monthly_limit = data.monthly_limit
        if "min_purchase_amount" in fields_set:
            rule.min_purchase_amount = data.min_purchase_amount
        if "start_date" in fields_set and data.start_date is not None:
            rule.start_date = data.start_date
        if "end_date" in fields_set:
            rule.end_date = data.end_date
        await self.session.flush()

        recalculated = 0
        if data.recalculate_existing:
            recalculated = await self._recalculate_for_rule(user_id, rule)

        await self.audit.log(
            "update", "cashback_rule", user_id=user_id, entity_id=rule.id, ip_address=ip
        )
        return rule, recalculated

    async def delete_rule(
        self,
        user_id: UUID,
        card_id: UUID,
        rule_id: UUID,
        ip: str | None = None,
    ) -> None:
        card = await self.card_repo.get_by_id_for_user(card_id, user_id)
        if card is None:
            raise NotFoundError("Card not found")
        rule = await self.rule_repo.get_by_id_for_card(rule_id, card_id)
        if rule is None:
            raise NotFoundError("Cashback rule not found")
        await self.rule_repo.delete(rule)
        await self.audit.log(
            "delete", "cashback_rule", user_id=user_id, entity_id=rule_id, ip_address=ip
        )

    async def _recalculate_for_rule(self, user_id: UUID, rule: CashbackRule) -> int:
        transactions = await self.tx_repo.list_expenses_for_cashback_recalc(
            user_id,
            rule.category_id,
            rule.card_id,
            rule.start_date,
            rule.end_date,
        )
        if not transactions:
            return 0
        tx_ids = [tx.id for tx in transactions]
        await self.accrual_repo.delete_for_card_transactions(
            rule.card_id, tx_ids, auto_only=True
        )
        await self.session.flush()
        recalculated = 0
        for tx in transactions:
            if not self._transaction_in_rule_period(tx, rule):
                continue
            await self.evaluate(
                user_id,
                tx,
                rule.category_id,
                str(rule.card_id),
                notify=False,
            )
            recalculated += 1
        return recalculated

    @staticmethod
    def _transaction_in_rule_period(transaction: Transaction, rule: CashbackRule) -> bool:
        on_date = transaction.transaction_date
        if on_date < rule.start_date:
            return False
        if rule.end_date is not None and on_date > rule.end_date:
            return False
        return True

    async def evaluate(
        self,
        user_id: UUID,
        transaction: Transaction,
        category_id: UUID,
        card_id: str | None,
        *,
        notify: bool = True,
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
            existing = await self.accrual_repo.get_for_transaction_card(
                transaction.id, card.id
            )
            if existing is not None and existing.rule_id is None:
                continue
            min_amt = rule.min_purchase_amount
            if min_amt is not None and transaction.amount < min_amt:
                continue
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
        manual = await self.accrual_repo.get_for_transaction_card(transaction.id, card.id)
        if manual is not None and manual.rule_id is None:
            return manual
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
        if notify:
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
        existing = await self.accrual_repo.get_for_transaction_card(transaction.id, card.id)
        if existing is not None:
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

    async def set_manual_cashback(
        self,
        user_id: UUID,
        transaction_id: UUID,
        amount: Decimal,
        card_id: UUID | None = None,
        ip: str | None = None,
    ) -> CashbackAccrual | None:
        tx = await self.tx_repo.get_by_id_for_user(transaction_id, user_id)
        if tx is None:
            raise NotFoundError("Transaction not found")
        if tx.type != TransactionType.EXPENSE:
            raise ValidationError("Cashback only applies to expense transactions")

        resolved_card_id = card_id or tx.card_id
        if resolved_card_id is None:
            raise ValidationError("card_id is required when transaction has no card")

        card = await self.card_repo.get_by_id_for_user(resolved_card_id, user_id)
        if card is None:
            raise NotFoundError("Card not found")

        if amount <= 0:
            await self.accrual_repo.delete_for_transaction(transaction_id, user_id)
            await self.audit.log(
                "delete",
                "cashback_accrual",
                user_id=user_id,
                entity_id=transaction_id,
                ip_address=ip,
            )
            return None

        period_month = tx.transaction_date.strftime("%Y-%m")
        existing = await self.accrual_repo.get_for_transaction_card(
            transaction_id, resolved_card_id
        )
        if existing is not None:
            existing.amount = amount
            existing.rule_id = None
            existing.status = CashbackAccrualStatus.ACCRUED
            existing.period_month = period_month
            await self.session.flush()
            accrual = existing
            action = "update"
        else:
            accrual = CashbackAccrual(
                user_id=user_id,
                transaction_id=transaction_id,
                card_id=resolved_card_id,
                rule_id=None,
                amount=amount,
                period_month=period_month,
                status=CashbackAccrualStatus.ACCRUED,
            )
            await self.accrual_repo.create(accrual)
            action = "create"

        await self.audit.log(
            action,
            "cashback_accrual",
            user_id=user_id,
            entity_id=accrual.id,
            payload={"amount": str(amount), "manual": True},
            ip_address=ip,
        )
        return accrual

    async def delete_cashback(
        self, user_id: UUID, transaction_id: UUID, ip: str | None = None
    ) -> None:
        tx = await self.tx_repo.get_by_id_for_user(transaction_id, user_id)
        if tx is None:
            raise NotFoundError("Transaction not found")
        await self.accrual_repo.delete_for_transaction(transaction_id, user_id)
        await self.audit.log(
            "delete",
            "cashback_accrual",
            user_id=user_id,
            entity_id=transaction_id,
            ip_address=ip,
        )

    async def get_payout_preview(
        self, user_id: UUID, period_month: str | None = None
    ) -> CashbackPayoutPreview:
        period = period_month or previous_period_month()
        cards = await self.card_repo.list_by_user(user_id)
        earned = await self.accrual_repo.earned_by_card(user_id, period)
        paid_card_ids = await self.payout_repo.list_paid_card_ids(user_id, period)
        return CashbackPayoutPreview(
            period_month=period,
            cards=[
                CashbackPayoutCardPreview(
                    card_id=str(card.id),
                    card_name=card.name,
                    account_id=str(card.account_id),
                    accrued_amount=earned.get(card.id, Decimal("0")),
                    already_paid_out=card.id in paid_card_ids,
                )
                for card in cards
            ],
        )

    async def accrue_payout(
        self, user_id: UUID, data: CashbackPayoutCreate, ip: str | None = None
    ) -> CashbackPayout:
        """Начислить накопленный за месяц кэшбэк как доходную транзакцию по карте."""
        period = data.period_month or previous_period_month()
        card = await self.card_repo.get_by_id_for_user(UUID(data.card_id), user_id)
        if card is None:
            raise NotFoundError("Card not found")

        existing = await self.payout_repo.get_for_card_period(card.id, period)
        if existing is not None:
            previous_tx = await self.tx_repo.get_by_id_for_user(existing.transaction_id, user_id)
            if previous_tx is not None:
                raise ConflictError(
                    f"Кэшбэк за {period} по карте «{card.name}» уже начислен"
                )
            # Транзакция удалена — прошлая выплата больше не действует, начисляем заново.
            await self.payout_repo.delete(existing)

        if data.amount is not None:
            amount = data.amount
        else:
            earned = await self.accrual_repo.earned_by_card(user_id, period)
            amount = earned.get(card.id, Decimal("0"))
        if amount <= 0:
            raise ValidationError(f"Нет накопленного кэшбэка за {period} по карте «{card.name}»")

        category = await self._get_or_create_cashback_category(user_id)
        transaction = await self._create_payout_transaction(user_id, card, category, period, amount)

        payout = CashbackPayout(
            user_id=user_id,
            card_id=card.id,
            transaction_id=transaction.id,
            period_month=period,
            amount=amount,
        )
        await self.payout_repo.create(payout)
        await self.audit.log(
            "create",
            "cashback_payout",
            user_id=user_id,
            entity_id=payout.id,
            payload={
                "card_id": str(card.id),
                "period_month": period,
                "amount": str(amount),
                "transaction_id": str(transaction.id),
            },
            ip_address=ip,
        )
        return payout

    async def _get_or_create_cashback_category(self, user_id: UUID) -> Category:
        category = await self.category_repo.find_by_name(
            user_id, CASHBACK_CATEGORY_NAME, CategoryType.INCOME
        )
        if category is not None:
            return category
        category = Category(
            user_id=user_id,
            name=CASHBACK_CATEGORY_NAME,
            type=CategoryType.INCOME,
            is_essential=False,
        )
        return await self.category_repo.create(category)

    async def _create_payout_transaction(
        self,
        user_id: UUID,
        card: Card,
        category: Category,
        period_month: str,
        amount: Decimal,
    ) -> Transaction:
        from app.services.ledger import TransactionService

        year, month = period_month.split("-")
        description = (
            f"Кэшбэк за {_MONTH_NAMES_GENITIVE[int(month) - 1]} {year} · {card.name}"
        )
        transaction = await TransactionService(self.session).create(
            user_id,
            TransactionCreate(
                account_id=str(card.account_id),
                category_id=str(category.id),
                type=TransactionType.INCOME,
                amount=amount,
                description=description,
                transaction_date=date.today(),
                card_id=str(card.id),
            ),
            run_cashback=False,
        )
        assert not isinstance(transaction, list)
        return transaction

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
                min_purchase_amount=best_rule.min_purchase_amount,
            )
        ]
