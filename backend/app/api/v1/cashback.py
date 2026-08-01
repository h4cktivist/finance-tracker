from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, DbSession, get_client_ip
from app.core.exceptions import NotFoundError
from app.core.responses import APIResponse
from app.models.cashback import CashbackAccrualStatus
from app.repositories.card import CardRepository, CashbackRuleRepository
from app.repositories.cashback import CashbackAccrualRepository
from app.schemas.cashback import (
    CardCreate,
    CardResponse,
    CashbackAccrualResponse,
    CashbackRecommendation,
    CashbackRuleCreate,
    CashbackRuleResponse,
    CashbackRuleUpdate,
    CashbackRuleUpdateResponse,
    CashbackSummaryResponse,
)
from app.services.cashback import CashbackService

router = APIRouter()


@router.post("/cards", response_model=APIResponse[CardResponse])
async def create_card(
    data: CardCreate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[CardResponse]:
    service = CashbackService(db)
    card = await service.create_card(user.id, data, ip=ip)
    return APIResponse(
        data=CardResponse(
            id=str(card.id),
            user_id=str(card.user_id),
            account_id=str(card.account_id),
            name=card.name,
            bank_name=card.bank_name,
            last_digits=card.last_digits,
        )
    )


@router.get("/cards", response_model=APIResponse[list[CardResponse]])
async def list_cards(user: CurrentUser, db: DbSession) -> APIResponse[list[CardResponse]]:
    repo = CardRepository(db)
    cards = await repo.list_by_user(user.id)
    return APIResponse(
        data=[
            CardResponse(
                id=str(c.id),
                user_id=str(c.user_id),
                account_id=str(c.account_id),
                name=c.name,
                bank_name=c.bank_name,
                last_digits=c.last_digits,
            )
            for c in cards
        ]
    )


@router.post("/cards/{card_id}/rules", response_model=APIResponse[CashbackRuleResponse])
async def create_rule(
    card_id: UUID,
    data: CashbackRuleCreate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[CashbackRuleResponse]:
    service = CashbackService(db)
    rule = await service.create_rule(user.id, card_id, data, ip=ip)
    return APIResponse(data=_rule_response(rule))


def _rule_response(rule) -> CashbackRuleResponse:
    return CashbackRuleResponse(
        id=str(rule.id),
        card_id=str(rule.card_id),
        category_id=str(rule.category_id),
        cashback_percent=rule.cashback_percent,
        monthly_limit=rule.monthly_limit,
        min_purchase_amount=rule.min_purchase_amount,
        start_date=rule.start_date,
        end_date=rule.end_date,
    )


@router.patch(
    "/cards/{card_id}/rules/{rule_id}",
    response_model=APIResponse[CashbackRuleUpdateResponse],
)
async def update_rule(
    card_id: UUID,
    rule_id: UUID,
    data: CashbackRuleUpdate,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[CashbackRuleUpdateResponse]:
    service = CashbackService(db)
    rule, recalculated = await service.update_rule(user.id, card_id, rule_id, data, ip=ip)
    return APIResponse(
        data=CashbackRuleUpdateResponse(
            rule=_rule_response(rule),
            recalculated_transactions=recalculated,
        )
    )


@router.delete("/cards/{card_id}/rules/{rule_id}", response_model=APIResponse[None])
async def delete_rule(
    card_id: UUID,
    rule_id: UUID,
    user: CurrentUser,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[None]:
    service = CashbackService(db)
    await service.delete_rule(user.id, card_id, rule_id, ip=ip)
    return APIResponse(data=None)


@router.get("/cards/{card_id}/rules", response_model=APIResponse[list[CashbackRuleResponse]])
async def list_rules(card_id: UUID, user: CurrentUser, db: DbSession) -> APIResponse:
    card_repo = CardRepository(db)
    card = await card_repo.get_by_id_for_user(card_id, user.id)
    if card is None:
        raise NotFoundError("Card not found")
    rule_repo = CashbackRuleRepository(db)
    rules = await rule_repo.list_for_card(card_id)
    return APIResponse(data=[_rule_response(r) for r in rules])


@router.get("/summary", response_model=APIResponse[CashbackSummaryResponse])
async def cashback_summary(
    user: CurrentUser, db: DbSession, period_month: str | None = None
) -> APIResponse[CashbackSummaryResponse]:
    repo = CashbackAccrualRepository(db)
    total = await repo.total_earned(user.id, period_month)
    return APIResponse(data=CashbackSummaryResponse(total_earned=total, period_month=period_month))


@router.get("/missed", response_model=APIResponse[list[CashbackAccrualResponse]])
async def missed_cashback(user: CurrentUser, db: DbSession) -> APIResponse:
    repo = CashbackAccrualRepository(db)
    accruals = await repo.list_by_user(user.id, status=CashbackAccrualStatus.MISSED)
    return APIResponse(
        data=[
            CashbackAccrualResponse(
                id=str(a.id),
                transaction_id=str(a.transaction_id),
                card_id=str(a.card_id),
                amount=a.amount,
                period_month=a.period_month,
                status=a.status,
                is_manual=a.rule_id is None,
            )
            for a in accruals
        ]
    )


@router.get("/recommendations", response_model=APIResponse[list[CashbackRecommendation]])
async def recommendations(
    user: CurrentUser, db: DbSession, category_id: UUID = Query(...)
) -> APIResponse[list[CashbackRecommendation]]:
    service = CashbackService(db)
    recs = await service.get_recommendations(user.id, category_id)
    return APIResponse(data=recs)
