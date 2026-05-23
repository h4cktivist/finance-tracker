from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.account import Account
from app.models.user import User
from app.repositories.account import AccountRepository
from app.repositories.ledger import LedgerRepository
from app.schemas.account import AccountCreate, AccountUpdate
from app.services.audit import AuditService


class AccountService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AccountRepository(session)
        self.ledger_repo = LedgerRepository(session)
        self.audit = AuditService(session)

    async def create(self, user: User, data: AccountCreate, ip: str | None = None) -> Account:
        account = Account(
            user_id=user.id, name=data.name, type=data.type, initial_balance=data.initial_balance
        )
        await self.repo.create(account)
        await self.audit.log(
            "create", "account", user_id=user.id, entity_id=account.id, ip_address=ip
        )
        return account

    async def list_with_balances(self, user_id: UUID) -> list[tuple[Account, Decimal]]:
        accounts = await self.repo.list_by_user(user_id)
        result = []
        for acc in accounts:
            balance = await self.ledger_repo.get_account_balance(acc.id, acc.initial_balance)
            result.append((acc, balance))
        return result

    async def get_balance(self, account_id: UUID, user_id: UUID) -> Decimal:
        account = await self.repo.get_by_id_for_user(account_id, user_id)
        if account is None:
            raise NotFoundError("Account not found")
        return await self.ledger_repo.get_account_balance(account.id, account.initial_balance)

    async def update(
        self, user_id: UUID, account_id: UUID, data: AccountUpdate, ip: str | None = None
    ) -> Account:
        account = await self.repo.get_by_id_for_user(account_id, user_id)
        if account is None:
            raise NotFoundError("Account not found")
        if data.name is not None:
            account.name = data.name
        if data.type is not None:
            account.type = data.type
        await self.session.flush()
        await self.audit.log(
            "update", "account", user_id=user_id, entity_id=account.id, ip_address=ip
        )
        return account

    async def delete(self, user_id: UUID, account_id: UUID, ip: str | None = None) -> None:
        account = await self.repo.get_by_id_for_user(account_id, user_id)
        if account is None:
            raise NotFoundError("Account not found")
        await self.repo.soft_delete(account)
        await self.audit.log(
            "delete", "account", user_id=user_id, entity_id=account.id, ip_address=ip
        )
