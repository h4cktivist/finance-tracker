import logging
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.recurring import RecurringFrequency, RecurringTransaction
from app.models.recurring_execution import RecurringExecution
from app.models.user import User
from app.repositories.account import AccountRepository
from app.repositories.category import CategoryRepository
from app.repositories.recurring import RecurringExecutionRepository, RecurringRepository
from app.schemas.recurring import RecurringCreate, RecurringUpdate
from app.schemas.transaction import TransactionCreate
from app.services.audit import AuditService
from app.services.ledger import TransactionService
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)


def advance_date(current: date, frequency: RecurringFrequency, interval: int) -> date:
    if frequency == RecurringFrequency.DAILY:
        return current + timedelta(days=interval)
    if frequency == RecurringFrequency.WEEKLY:
        return current + timedelta(weeks=interval)
    if frequency == RecurringFrequency.MONTHLY:
        month_index = current.month - 1 + interval
        year = current.year + month_index // 12
        month = month_index % 12 + 1
        day = min(current.day, 28)
        return date(year, month, day)
    year = current.year + interval
    return date(year, current.month, min(current.day, 28))


class RecurringService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = RecurringRepository(session)
        self.execution_repo = RecurringExecutionRepository(session)
        self.account_repo = AccountRepository(session)
        self.category_repo = CategoryRepository(session)
        self.tx_service = TransactionService(session)
        self.audit = AuditService(session)
        self.notifications = NotificationService(session)

    async def create(
        self, user: User, data: RecurringCreate, ip: str | None = None
    ) -> RecurringTransaction:
        account = await self.account_repo.get_by_id_for_user(UUID(data.account_id), user.id)
        if account is None:
            raise NotFoundError("Account not found")
        category_id: UUID | None = None
        if data.category_id:
            category = await self.category_repo.get_by_id_for_user(UUID(data.category_id), user.id)
            if category is None:
                raise NotFoundError("Category not found")
            category_id = category.id
        recurring = RecurringTransaction(
            user_id=user.id,
            frequency=data.frequency,
            interval=data.interval,
            start_date=data.start_date,
            end_date=data.end_date,
            next_execution_date=data.start_date,
            account_id=account.id,
            category_id=category_id,
            type=data.type,
            amount=data.amount,
            description=data.description,
            merchant_name=data.merchant_name,
            notes=data.notes,
        )
        await self.repo.create(recurring)
        await self.audit.log(
            "create", "recurring", user_id=user.id, entity_id=recurring.id, ip_address=ip
        )
        return recurring

    async def process_due(self, as_of: date | None = None) -> int:
        as_of = as_of or date.today()
        due_list = await self.repo.list_due(as_of)
        processed = 0
        for recurring in due_list:
            try:
                if recurring.end_date and recurring.next_execution_date > recurring.end_date:
                    recurring.is_active = False
                    continue
                if await self.execution_repo.exists(recurring.id, recurring.next_execution_date):
                    recurring.next_execution_date = advance_date(
                        recurring.next_execution_date, recurring.frequency, recurring.interval
                    )
                    continue
                tx_data = TransactionCreate(
                    account_id=str(recurring.account_id),
                    category_id=str(recurring.category_id) if recurring.category_id else None,
                    type=recurring.type,
                    amount=recurring.amount,
                    description=recurring.description or "Recurring transaction",
                    merchant_name=recurring.merchant_name,
                    transaction_date=recurring.next_execution_date,
                    notes=recurring.notes,
                )
                tx = await self.tx_service.create(recurring.user_id, tx_data)
                tx_id = tx.id if not isinstance(tx, list) else tx[0].id
                execution = RecurringExecution(
                    recurring_id=recurring.id,
                    execution_date=recurring.next_execution_date,
                    transaction_id=tx_id,
                )
                await self.execution_repo.create(execution)
                await self.notifications.notify_recurring_created(recurring.user_id, recurring)
                recurring.next_execution_date = advance_date(
                    recurring.next_execution_date, recurring.frequency, recurring.interval
                )
                processed += 1
            except Exception:
                logger.exception("Failed to process recurring transaction %s", recurring.id)
                continue
        return processed

    async def update(
        self, user_id: UUID, recurring_id: UUID, data: RecurringUpdate, ip: str | None = None
    ) -> RecurringTransaction:
        recurring = await self.repo.get_by_id_for_user(recurring_id, user_id)
        if recurring is None:
            raise NotFoundError("Recurring transaction not found")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(recurring, field, value)
        await self.session.flush()
        await self.audit.log(
            "update", "recurring", user_id=user_id, entity_id=recurring.id, ip_address=ip
        )
        return recurring
