from typing import Annotated

from fastapi import APIRouter, Header

from app.core.deps import CurrentUser
from app.core.responses import APIResponse
from app.schemas.broker import BrokerPortfolio, BrokerRecommendationsResponse
from app.services.broker import BrokerCredentialsMissingError, BrokerService
from app.services.broker_recommendations import BrokerRecommendationsService

router = APIRouter()


@router.get("/portfolio", response_model=APIResponse[BrokerPortfolio])
async def get_portfolio(
    user: CurrentUser,
    x_finam_token: Annotated[str | None, Header()] = None,
    x_finam_account_id: Annotated[str | None, Header()] = None,
) -> APIResponse[BrokerPortfolio]:
    if not x_finam_token or not x_finam_account_id:
        raise BrokerCredentialsMissingError()
    service = BrokerService(api_token=x_finam_token, account_id=x_finam_account_id)
    portfolio = await service.get_portfolio()
    return APIResponse(data=portfolio)


@router.post("/recommendations", response_model=APIResponse[BrokerRecommendationsResponse])
async def get_broker_recommendations(
    user: CurrentUser,
    x_finam_token: Annotated[str | None, Header()] = None,
    x_finam_account_id: Annotated[str | None, Header()] = None,
) -> APIResponse[BrokerRecommendationsResponse]:
    if not x_finam_token or not x_finam_account_id:
        raise BrokerCredentialsMissingError()
    portfolio = await BrokerService(
        api_token=x_finam_token, account_id=x_finam_account_id
    ).get_portfolio()
    content = await BrokerRecommendationsService().generate(portfolio)
    return APIResponse(
        data=BrokerRecommendationsResponse(account_id=portfolio.account_id, content=content),
        message="Рекомендации по портфелю сгенерированы",
    )
