from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, DbSession, get_client_ip
from app.core.exceptions import NotFoundError
from app.core.responses import APIResponse
from app.repositories.account import AccountRepository
from app.schemas.account import AccountCreate, AccountResponse, AccountUpdate
from app.services.account import AccountService

router = APIRouter()


def _account_response(acc, balance=None) -> AccountResponse:
    return AccountResponse(
        id=str(acc.id),
        user_id=str(acc.user_id),
        name=acc.name,
        type=acc.type,
        initial_balance=acc.initial_balance,
        balance=balance,
        created_at=acc.created_at,
        updated_at=acc.updated_at,
    )


@router.post("", response_model=APIResponse[AccountResponse])
async def create_account(
    data: AccountCreate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[AccountResponse]:
    service = AccountService(db)
    account = await service.create(user, data, ip=ip)
    balance = await service.get_balance(account.id, user.id)
    return APIResponse(data=_account_response(account, balance))


@router.get("", response_model=APIResponse[list[AccountResponse]])
async def list_accounts(user: CurrentUser, db: DbSession) -> APIResponse[list[AccountResponse]]:
    service = AccountService(db)
    items = await service.list_with_balances(user.id)
    return APIResponse(data=[_account_response(acc, bal) for (acc, bal) in items])


@router.get("/{account_id}", response_model=APIResponse[AccountResponse])
async def get_account(
    account_id: UUID, user: CurrentUser, db: DbSession
) -> APIResponse[AccountResponse]:
    repo = AccountRepository(db)
    account = await repo.get_by_id_for_user(account_id, user.id)
    if account is None:
        raise NotFoundError("Account not found")
    service = AccountService(db)
    balance = await service.get_balance(account_id, user.id)
    return APIResponse(data=_account_response(account, balance))


@router.patch("/{account_id}", response_model=APIResponse[AccountResponse])
async def update_account(
    account_id: UUID,
    data: AccountUpdate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[AccountResponse]:
    service = AccountService(db)
    account = await service.update(user.id, account_id, data, ip=ip)
    balance = await service.get_balance(account_id, user.id)
    return APIResponse(data=_account_response(account, balance))


@router.delete("/{account_id}", response_model=APIResponse[None])
async def delete_account(
    account_id: UUID,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[None]:
    service = AccountService(db)
    await service.delete(user.id, account_id, ip=ip)
    return APIResponse(message="Account deleted")
