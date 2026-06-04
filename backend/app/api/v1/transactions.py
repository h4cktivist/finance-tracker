from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, DbSession, get_client_ip
from app.core.exceptions import NotFoundError
from app.core.responses import APIResponse
from app.models.transaction import Transaction, TransactionType
from app.repositories.cashback import CashbackAccrualRepository
from app.repositories.tag import TagRepository
from app.repositories.transaction import TransactionRepository
from app.schemas.transaction import (
    CorrectionCreate,
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdate,
)
from app.services.ledger import TransactionService

router = APIRouter()


def _cashback_for_expense(
    tx: Transaction, accrued: dict[UUID, Decimal]
) -> Decimal | None:
    if tx.type != TransactionType.EXPENSE:
        return None
    amount = accrued.get(tx.id, Decimal("0"))
    return amount if amount > 0 else None


async def _load_cashback_map(db, transactions: list[Transaction]) -> dict[UUID, Decimal]:
    expense_ids = [tx.id for tx in transactions if tx.type == TransactionType.EXPENSE]
    if not expense_ids:
        return {}
    repo = CashbackAccrualRepository(db)
    return await repo.sum_accrued_by_transaction_ids(expense_ids)


async def _tx_response(
    db,
    tx: Transaction,
    *,
    cashback_by_tx: dict[UUID, Decimal] | None = None,
) -> TransactionResponse:
    tag_repo = TagRepository(db)
    tag_ids = [str(t) for t in await tag_repo.get_transaction_tag_ids(tx.id)]
    if cashback_by_tx is None:
        cashback_by_tx = await _load_cashback_map(db, [tx])
    return TransactionResponse(
        id=str(tx.id),
        user_id=str(tx.user_id),
        account_id=str(tx.account_id),
        category_id=str(tx.category_id) if tx.category_id else None,
        type=tx.type,
        amount=tx.amount,
        description=tx.description,
        merchant_name=tx.merchant_name,
        transaction_date=tx.transaction_date,
        notes=tx.notes,
        transfer_group_id=str(tx.transfer_group_id) if tx.transfer_group_id else None,
        correction_of_id=str(tx.correction_of_id) if tx.correction_of_id else None,
        card_id=str(tx.card_id) if tx.card_id else None,
        tag_ids=tag_ids,
        cashback_amount=_cashback_for_expense(tx, cashback_by_tx),
        created_at=tx.created_at,
        updated_at=tx.updated_at,
    )


@router.post("", response_model=APIResponse[TransactionResponse | list[TransactionResponse]])
async def create_transaction(
    data: TransactionCreate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse:
    service = TransactionService(db)
    result = await service.create(user.id, data, ip=ip)
    if isinstance(result, list):
        cashback_by_tx = await _load_cashback_map(db, result)
        return APIResponse(
            data=[await _tx_response(db, tx, cashback_by_tx=cashback_by_tx) for tx in result],
            message="Transfer created",
        )
    return APIResponse(data=await _tx_response(db, result))


@router.get("", response_model=APIResponse[TransactionListResponse])
async def list_transactions(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: TransactionType | None = None,
    account_id: UUID | None = None,
    category_id: UUID | None = None,
    tag_id: UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
    sort_by: str = "transaction_date",
    sort_order: str = "desc",
) -> APIResponse[TransactionListResponse]:
    repo = TransactionRepository(db)
    items, total = await repo.list_filtered(
        user.id,
        page=page,
        page_size=page_size,
        type_filter=type,
        account_id=account_id,
        category_id=category_id,
        tag_id=tag_id,
        date_from=date_from,
        date_to=date_to,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    pages = (total + page_size - 1) // page_size if page_size else 0
    cashback_by_tx = await _load_cashback_map(db, items)
    return APIResponse(
        data=TransactionListResponse(
            items=[
                await _tx_response(db, tx, cashback_by_tx=cashback_by_tx) for tx in items
            ],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
    )


@router.get("/{transaction_id}", response_model=APIResponse[TransactionResponse])
async def get_transaction(
    transaction_id: UUID, user: CurrentUser, db: DbSession
) -> APIResponse[TransactionResponse]:
    repo = TransactionRepository(db)
    tx = await repo.get_by_id_for_user(transaction_id, user.id)
    if tx is None:
        raise NotFoundError("Transaction not found")
    return APIResponse(data=await _tx_response(db, tx))


@router.patch("/{transaction_id}", response_model=APIResponse[TransactionResponse])
async def update_transaction(
    transaction_id: UUID,
    data: TransactionUpdate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[TransactionResponse]:
    service = TransactionService(db)
    tx = await service.update_metadata(user.id, transaction_id, data, ip=ip)
    return APIResponse(data=await _tx_response(db, tx))


@router.delete("/{transaction_id}", response_model=APIResponse[None])
async def delete_transaction(
    transaction_id: UUID,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[None]:
    service = TransactionService(db)
    await service.soft_delete(user.id, transaction_id, ip=ip)
    return APIResponse(message="Transaction deleted")


@router.post("/{transaction_id}/correct", response_model=APIResponse[TransactionResponse])
async def correct_transaction(
    transaction_id: UUID,
    data: CorrectionCreate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[TransactionResponse]:
    service = TransactionService(db)
    tx = await service.create_correction(user.id, transaction_id, data, ip=ip)
    return APIResponse(data=await _tx_response(db, tx))
