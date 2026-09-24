from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.v1.transactions import _load_cashback_map, _tx_response
from app.core.deps import CurrentUser, DbSession, get_client_ip
from app.core.responses import APIResponse
from app.models.transaction_template import TransactionTemplate
from app.repositories.transaction_template import TransactionTemplateRepository
from app.schemas.transaction import TransactionResponse
from app.schemas.transaction_template import (
    TemplateApply,
    TemplateCreate,
    TemplateFromTransaction,
    TemplateResponse,
    TemplateUpdate,
)
from app.services.transaction_template import TransactionTemplateService

router = APIRouter()


def _template_response(t: TransactionTemplate) -> TemplateResponse:
    return TemplateResponse(
        id=str(t.id),
        name=t.name,
        account_id=str(t.account_id),
        target_account_id=str(t.target_account_id) if t.target_account_id else None,
        category_id=str(t.category_id) if t.category_id else None,
        card_id=str(t.card_id) if t.card_id else None,
        type=t.type,
        amount=t.amount,
        description=t.description,
        merchant_name=t.merchant_name,
        notes=t.notes,
        tag_ids=list(t.tag_ids or []),
        created_at=t.created_at,
    )


@router.get("", response_model=APIResponse[list[TemplateResponse]])
async def list_templates(user: CurrentUser, db: DbSession) -> APIResponse[list[TemplateResponse]]:
    repo = TransactionTemplateRepository(db)
    items = await repo.list_by_user(user.id)
    return APIResponse(data=[_template_response(t) for t in items])


@router.post("", response_model=APIResponse[TemplateResponse])
async def create_template(
    data: TemplateCreate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[TemplateResponse]:
    service = TransactionTemplateService(db)
    template = await service.create(user.id, data, ip=ip)
    return APIResponse(data=_template_response(template))


@router.post("/from-transaction/{transaction_id}", response_model=APIResponse[TemplateResponse])
async def create_template_from_transaction(
    transaction_id: UUID,
    user: CurrentUser,
    db: DbSession,
    data: TemplateFromTransaction | None = None,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[TemplateResponse]:
    service = TransactionTemplateService(db)
    template = await service.create_from_transaction(
        user.id, transaction_id, data or TemplateFromTransaction(), ip=ip
    )
    return APIResponse(data=_template_response(template), message="Template created")


@router.patch("/{template_id}", response_model=APIResponse[TemplateResponse])
async def update_template(
    template_id: UUID,
    data: TemplateUpdate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[TemplateResponse]:
    service = TransactionTemplateService(db)
    template = await service.update(user.id, template_id, data, ip=ip)
    return APIResponse(data=_template_response(template))


@router.delete("/{template_id}", response_model=APIResponse[None])
async def delete_template(
    template_id: UUID,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[None]:
    service = TransactionTemplateService(db)
    await service.delete(user.id, template_id, ip=ip)
    return APIResponse(message="Template deleted")


@router.post(
    "/{template_id}/apply",
    response_model=APIResponse[TransactionResponse | list[TransactionResponse]],
)
async def apply_template(
    template_id: UUID,
    user: CurrentUser,
    db: DbSession,
    data: TemplateApply | None = None,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse:
    service = TransactionTemplateService(db)
    result = await service.apply(user.id, template_id, data or TemplateApply(), ip=ip)
    if isinstance(result, list):
        cashback_by_tx = await _load_cashback_map(db, result)
        return APIResponse(
            data=[await _tx_response(db, tx, cashback_by_tx=cashback_by_tx) for tx in result],
            message="Transfer created",
        )
    return APIResponse(data=await _tx_response(db, result), message="Transaction created")
