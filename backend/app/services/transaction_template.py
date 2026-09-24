from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.ledger import LedgerEntry, LedgerSide
from app.models.transaction import Transaction, TransactionType
from app.models.transaction_template import TransactionTemplate
from app.repositories.account import AccountRepository
from app.repositories.card import CardRepository
from app.repositories.category import CategoryRepository
from app.repositories.tag import TagRepository
from app.repositories.transaction import TransactionRepository
from app.repositories.transaction_template import TransactionTemplateRepository
from app.schemas.transaction import TransactionCreate
from app.schemas.transaction_template import (
    TemplateApply,
    TemplateCreate,
    TemplateFromTransaction,
    TemplateUpdate,
)
from app.services.audit import AuditService
from app.services.ledger import TransactionService

_DEFAULT_NAMES = {
    TransactionType.EXPENSE: "Расход",
    TransactionType.INCOME: "Доход",
    TransactionType.TRANSFER: "Перевод",
}


class TransactionTemplateService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TransactionTemplateRepository(session)
        self.tx_repo = TransactionRepository(session)
        self.account_repo = AccountRepository(session)
        self.category_repo = CategoryRepository(session)
        self.card_repo = CardRepository(session)
        self.tag_repo = TagRepository(session)
        self.tx_service = TransactionService(session)
        self.audit = AuditService(session)

    async def _get(self, user_id: UUID, template_id: UUID) -> TransactionTemplate:
        template = await self.repo.get_by_id_for_user(template_id, user_id)
        if template is None:
            raise NotFoundError("Template not found")
        return template

    async def create(
        self, user_id: UUID, data: TemplateCreate, ip: str | None = None
    ) -> TransactionTemplate:
        # Валидируем связи тем же кодом, что и при создании транзакции.
        probe = TransactionCreate(
            **data.model_dump(exclude={"name"}), transaction_date=date.today()
        )
        account = await self.account_repo.get_by_id_for_user(UUID(data.account_id), user_id)
        if account is None:
            raise NotFoundError("Account not found")
        await self.tx_service._validate_relations(user_id, probe)
        if data.target_account_id:
            target = await self.account_repo.get_by_id_for_user(
                UUID(data.target_account_id), user_id
            )
            if target is None:
                raise NotFoundError("Target account not found")
            if target.id == account.id:
                raise ValidationError("Cannot transfer to the same account")
        is_transfer = data.type == TransactionType.TRANSFER
        template = TransactionTemplate(
            user_id=user_id,
            name=data.name.strip(),
            account_id=account.id,
            target_account_id=UUID(data.target_account_id) if data.target_account_id else None,
            category_id=UUID(data.category_id) if data.category_id and not is_transfer else None,
            card_id=(
                UUID(data.card_id)
                if data.card_id and data.type == TransactionType.EXPENSE
                else None
            ),
            type=data.type,
            amount=data.amount,
            description=data.description,
            merchant_name=data.merchant_name,
            notes=data.notes,
            tag_ids=list(dict.fromkeys(data.tag_ids)),
        )
        await self.repo.create(template)
        await self.audit.log(
            "create", "transaction_template", user_id=user_id, entity_id=template.id, ip_address=ip
        )
        return template

    async def create_from_transaction(
        self,
        user_id: UUID,
        transaction_id: UUID,
        data: TemplateFromTransaction,
        ip: str | None = None,
    ) -> TransactionTemplate:
        tx = await self.tx_repo.get_by_id_for_user(transaction_id, user_id)
        if tx is None:
            raise NotFoundError("Transaction not found")
        account_id = tx.account_id
        target_account_id: UUID | None = None
        description = tx.description
        if tx.type == TransactionType.TRANSFER:
            account_id, target_account_id = await self._transfer_accounts(user_id, tx)
            description = await self._custom_transfer_description(
                user_id, description, account_id, target_account_id
            )
        tag_ids = [str(t) for t in await self.tag_repo.get_transaction_tag_ids(tx.id)]
        name = (data.name or "").strip() or (
            tx.description or tx.merchant_name or _DEFAULT_NAMES[tx.type]
        )
        create_data = TemplateCreate(
            name=name[:255],
            account_id=str(account_id),
            target_account_id=str(target_account_id) if target_account_id else None,
            category_id=str(tx.category_id) if tx.category_id else None,
            card_id=str(tx.card_id) if tx.card_id else None,
            type=tx.type,
            amount=tx.amount,
            description=description,
            merchant_name=tx.merchant_name,
            notes=tx.notes,
            tag_ids=tag_ids,
        )
        return await self.create(user_id, create_data, ip)

    async def _transfer_accounts(self, user_id: UUID, tx: Transaction) -> tuple[UUID, UUID]:
        """Возвращает (счёт списания, счёт зачисления) для любой из двух ног перевода."""
        if tx.transfer_group_id is None:
            raise ValidationError("Transfer has no counterpart")
        result = await self.session.execute(
            select(Transaction.account_id, LedgerEntry.side)
            .join(LedgerEntry, LedgerEntry.transaction_id == Transaction.id)
            .where(
                Transaction.user_id == user_id,
                Transaction.transfer_group_id == tx.transfer_group_id,
                Transaction.deleted_at.is_(None),
            )
        )
        sides = {side: account_id for account_id, side in result.all()}
        source = sides.get(LedgerSide.DEBIT)
        target = sides.get(LedgerSide.CREDIT)
        if source is None or target is None:
            raise ValidationError("Transfer has no counterpart")
        return source, target

    async def _custom_transfer_description(
        self, user_id: UUID, description: str | None, source_id: UUID, target_id: UUID
    ) -> str | None:
        """Автоописания «Transfer to/from …» не переносим: у каждой ноги оно своё."""
        if not description:
            return None
        source = await self.account_repo.get_by_id_for_user(source_id, user_id)
        target = await self.account_repo.get_by_id_for_user(target_id, user_id)
        auto = {
            f"Transfer to {target.name}" if target else None,
            f"Transfer from {source.name}" if source else None,
        }
        return None if description in auto else description

    async def update(
        self, user_id: UUID, template_id: UUID, data: TemplateUpdate, ip: str | None = None
    ) -> TransactionTemplate:
        template = await self._get(user_id, template_id)
        if data.name is not None:
            template.name = data.name.strip()
        if data.amount is not None:
            template.amount = data.amount
        await self.session.flush()
        await self.audit.log(
            "update", "transaction_template", user_id=user_id, entity_id=template.id, ip_address=ip
        )
        return template

    async def delete(self, user_id: UUID, template_id: UUID, ip: str | None = None) -> None:
        template = await self._get(user_id, template_id)
        await self.repo.delete(template)
        await self.audit.log(
            "delete", "transaction_template", user_id=user_id, entity_id=template_id, ip_address=ip
        )

    async def apply(
        self, user_id: UUID, template_id: UUID, data: TemplateApply, ip: str | None = None
    ) -> Transaction | list[Transaction]:
        template = await self._get(user_id, template_id)
        # Категории, карты и теги могли удалить после создания шаблона —
        # операцию всё равно создаём, просто без них.
        category_id = template.category_id
        if (
            category_id
            and await self.category_repo.get_by_id_for_user(category_id, user_id) is None
        ):
            category_id = None
        card_id = template.card_id
        if card_id and await self.card_repo.get_by_id_for_user(card_id, user_id) is None:
            card_id = None
        tag_ids = [
            t
            for t in template.tag_ids
            if await self.tag_repo.get_by_id_for_user(UUID(t), user_id) is not None
        ]
        tx_data = TransactionCreate(
            account_id=str(template.account_id),
            target_account_id=(
                str(template.target_account_id) if template.target_account_id else None
            ),
            category_id=str(category_id) if category_id else None,
            card_id=str(card_id) if card_id else None,
            type=template.type,
            amount=data.amount or template.amount,
            description=template.description,
            merchant_name=template.merchant_name,
            notes=template.notes,
            tag_ids=tag_ids,
            transaction_date=data.transaction_date or date.today(),
        )
        return await self.tx_service.create(user_id, tx_data, ip)
