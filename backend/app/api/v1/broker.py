from fastapi import APIRouter

from app.core.deps import CurrentUser
from app.core.responses import APIResponse
from app.schemas.broker import BrokerPortfolio
from app.services.broker import BrokerService

router = APIRouter()


@router.get("/portfolio", response_model=APIResponse[BrokerPortfolio])
async def get_portfolio(user: CurrentUser) -> APIResponse[BrokerPortfolio]:
    service = BrokerService()
    portfolio = await service.get_portfolio()
    return APIResponse(data=portfolio)
