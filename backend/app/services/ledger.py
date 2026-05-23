from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.ledger import LedgerEntry, LedgerSide
from app.models.transaction import Transaction, TransactionType
from app.repositories.account import AccountRepository
from app.repositories.card import CardRepository
from app.repositories.category import CategoryRepository
from app.repositories.ledger import LedgerRepository
from app.repositories.tag import TagRepository
from app.repositories.transaction import TransactionRepository
from app.schemas.transaction import CorrectionCreate, TransactionCreate, TransactionUpdate
from app.services.audit import AuditService


class TransactionService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tx_repo = TransactionRepository(session)
        self.account_repo = AccountRepository(session)
        self.category_repo = CategoryRepository(session)
        self.card_repo = CardRepository(session)
        self.ledger_repo = LedgerRepository(session)
        self.tag_repo = TagRepository(session)
        self.audit = AuditService(session)
        self._cashback_service = None

    def _get_cashback_service(self):
        if self._cashback_service is None:
            from app.services.cashback import CashbackService

            self._cashback_service = CashbackService(self.session)
        return self._cashback_service

    async def _validate_relations(self, user_id: UUID, data: TransactionCreate) -> None:
        if data.category_id:
            category = await self.category_repo.get_by_id_for_user(UUID(data.category_id), user_id)
            if category is None:
                raise NotFoundError("Category not found")
            if data.type == TransactionType.EXPENSE and category.type.value != "expense":
                raise ValidationError("Category type must be 'expense' for expense transactions")
            if data.type == TransactionType.INCOME and category.type.value != "income":
                raise ValidationError("Category type must be 'income' for income transactions")
        if data.card_id:
            card = await self.card_repo.get_by_id_for_user(UUID(data.card_id), user_id)
            if card is None:
                raise NotFoundError("Card not found")

    async def create(
        self,
        user_id: UUID,
        data: TransactionCreate,
        ip: str | None = None,
        *,
        run_cashback: bool = True,
    ) -> Transaction | list[Transaction]:
        account = await self.account_repo.get_by_id_for_user(UUID(data.account_id), user_id)
        if account is None:
            raise NotFoundError("Account not found")
        await self._validate_relations(user_id, data)
        if data.type == TransactionType.TRANSFER:
            return await self._create_transfer(user_id, data, ip)
        tx = Transaction(
            user_id=user_id,
            account_id=account.id,
            category_id=UUID(data.category_id) if data.category_id else None,
            type=data.type,
            amount=data.amount,
            description=data.description,
            merchant_name=data.merchant_name,
            transaction_date=data.transaction_date,
            notes=data.notes,
            card_id=UUID(data.card_id) if data.card_id else None,
        )
        await self.tx_repo.create(tx)
        side = LedgerSide.CREDIT if data.type == TransactionType.INCOME else LedgerSide.DEBIT
        await self._add_ledger(tx.id, account.id, data.amount, side)
        if data.tag_ids:
            await self.tag_repo.set_transaction_tags(tx.id, [UUID(t) for t in data.tag_ids])
        await self.audit.log(
            "create",
            "transaction",
            user_id=user_id,
            entity_id=tx.id,
            payload={"type": data.type.value, "amount": str(data.amount)},
            ip_address=ip,
        )
        if run_cashback and data.type == TransactionType.EXPENSE and data.category_id:
            await self._get_cashback_service().evaluate(
                user_id, tx, UUID(data.category_id), data.card_id
            )
        return tx

    async def _create_transfer(
        self, user_id: UUID, data: TransactionCreate, ip: str | None
    ) -> list[Transaction]:
        source = await self.account_repo.get_by_id_for_user(UUID(data.account_id), user_id)
        if not data.target_account_id:
            raise ValidationError("target_account_id is required for transfers")
        target = await self.account_repo.get_by_id_for_user(UUID(data.target_account_id), user_id)
        if source is None or target is None:
            raise NotFoundError("Source or target account not found")
        if source.id == target.id:
            raise ValidationError("Cannot transfer to the same account")
        group_id = uuid4()
        out_tx = Transaction(
            user_id=user_id,
            account_id=source.id,
            type=TransactionType.TRANSFER,
            amount=data.amount,
            description=data.description or f"Transfer to {target.name}",
            transaction_date=data.transaction_date,
            transfer_group_id=group_id,
        )
        in_tx = Transaction(
            user_id=user_id,
            account_id=target.id,
            type=TransactionType.TRANSFER,
            amount=data.amount,
            description=data.description or f"Transfer from {source.name}",
            transaction_date=data.transaction_date,
            transfer_group_id=group_id,
        )
        await self.tx_repo.create(out_tx)
        await self.tx_repo.create(in_tx)
        await self._add_ledger(out_tx.id, source.id, data.amount, LedgerSide.DEBIT)
        await self._add_ledger(in_tx.id, target.id, data.amount, LedgerSide.CREDIT)
        await self.audit.log(
            "create",
            "transfer",
            user_id=user_id,
            entity_id=group_id,
            payload={"amount": str(data.amount)},
            ip_address=ip,
        )
        return [out_tx, in_tx]

    async def _add_ledger(
        self, transaction_id: UUID, account_id: UUID, amount: Decimal, side: LedgerSide
    ) -> LedgerEntry:
        entry = LedgerEntry(
            transaction_id=transaction_id, account_id=account_id, amount=amount, side=side
        )
        return await self.ledger_repo.create(entry)

    async def update_metadata(
        self, user_id: UUID, transaction_id: UUID, data: TransactionUpdate, ip: str | None = None
    ) -> Transaction:
        tx = await self.tx_repo.get_by_id_for_user(transaction_id, user_id)
        if tx is None:
            raise NotFoundError("Transaction not found")
        if data.description is not None:
            tx.description = data.description
        if data.merchant_name is not None:
            tx.merchant_name = data.merchant_name
        if data.notes is not None:
            tx.notes = data.notes
        if data.tag_ids is not None:
            await self.tag_repo.set_transaction_tags(tx.id, [UUID(t) for t in data.tag_ids])
        await self.session.flush()
        await self.audit.log(
            "update", "transaction", user_id=user_id, entity_id=tx.id, ip_address=ip
        )
        return tx

    async def soft_delete(
        self, user_id: UUID, transaction_id: UUID, ip: str | None = None
    ) -> Transaction:
        tx = await self.tx_repo.get_by_id_for_user(transaction_id, user_id)
        if tx is None:
            raise NotFoundError("Transaction not found")
        await self.tx_repo.soft_delete(tx)
        if tx.transfer_group_id:
            result = await self.session.execute(
                select(Transaction).where(
                    Transaction.transfer_group_id == tx.transfer_group_id,
                    Transaction.deleted_at.is_(None),
                    Transaction.id != tx.id,
                )
            )
            for related in result.scalars().all():
                await self.tx_repo.soft_delete(related)
        await self.audit.log(
            "delete", "transaction", user_id=user_id, entity_id=tx.id, ip_address=ip
        )
        return tx

    async def create_correction(
        self, user_id: UUID, transaction_id: UUID, data: CorrectionCreate, ip: str | None = None
    ) -> Transaction:
        original = await self.tx_repo.get_by_id_for_user(transaction_id, user_id)
        if original is None:
            raise NotFoundError("Transaction not found")
        if original.type == TransactionType.TRANSFER:
            raise ValidationError("Use manual transfer correction for transfers")
        await self.soft_delete(user_id, transaction_id, ip)
        create_data = TransactionCreate(
            account_id=str(data.new_account_id or original.account_id),
            category_id=(
                str(data.new_category_id or original.category_id)
                if data.new_category_id or original.category_id
                else None
            ),
            type=original.type,
            amount=data.new_amount or original.amount,
            description=original.description,
            merchant_name=original.merchant_name,
            transaction_date=original.transaction_date,
            notes=f"Correction: {data.reason}. {original.notes or ''}".strip(),
            card_id=str(original.card_id) if original.card_id else None,
        )
        result = await self.create(user_id, create_data, ip, run_cashback=False)
        assert not isinstance(result, list)
        result.correction_of_id = original.id
        await self.session.flush()
        await self.audit.log(
            "correct",
            "transaction",
            user_id=user_id,
            entity_id=result.id,
            payload={"original_id": str(original.id), "reason": data.reason},
            ip_address=ip,
        )
        return result
