from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account, AccountType
from app.models.ledger import LedgerEntry, LedgerSide
from app.models.tag import Tag
from app.models.transaction import Transaction, TransactionType
from app.models.user import User


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> User:
    user = User(email="invariants@example.com", hashed_password="x")
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.mark.asyncio
async def test_partial_unique_tag_allows_reuse_after_soft_delete(
    db_session: AsyncSession, user: User
) -> None:
    tag = Tag(user_id=user.id, name="vacation")
    db_session.add(tag)
    await db_session.flush()
    from datetime import UTC, datetime

    tag.deleted_at = datetime.now(UTC)
    await db_session.flush()
    second = Tag(user_id=user.id, name="vacation")
    db_session.add(second)
    await db_session.flush()


@pytest.mark.asyncio
async def test_partial_unique_tag_blocks_two_active(db_session: AsyncSession, user: User) -> None:
    db_session.add(Tag(user_id=user.id, name="travel"))
    await db_session.flush()
    db_session.add(Tag(user_id=user.id, name="travel"))
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_ledger_entry_amount_must_be_positive(db_session: AsyncSession, user: User) -> None:
    from datetime import date

    account = Account(
        user_id=user.id, name="Acc", type=AccountType.CASH, initial_balance=Decimal("0")
    )
    db_session.add(account)
    await db_session.flush()
    tx = Transaction(
        user_id=user.id,
        account_id=account.id,
        type=TransactionType.EXPENSE,
        amount=Decimal("10"),
        transaction_date=date.today(),
    )
    db_session.add(tx)
    await db_session.flush()
    db_session.add(
        LedgerEntry(
            transaction_id=tx.id, account_id=account.id, amount=Decimal("0"), side=LedgerSide.DEBIT
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_transaction_amount_must_be_positive(db_session: AsyncSession, user: User) -> None:
    from datetime import date

    account = Account(
        user_id=user.id, name="Acc", type=AccountType.CASH, initial_balance=Decimal("0")
    )
    db_session.add(account)
    await db_session.flush()
    db_session.add(
        Transaction(
            user_id=user.id,
            account_id=account.id,
            type=TransactionType.EXPENSE,
            amount=Decimal("-5"),
            transaction_date=date.today(),
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()
