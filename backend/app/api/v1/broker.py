from typing import Annotated

from fastapi import APIRouter, Header

from app.core.deps import CurrentUser
from app.core.responses import APIResponse
from app.schemas.broker import BrokerPortfolio
from app.services.broker import BrokerCredentialsMissingError, BrokerService

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
