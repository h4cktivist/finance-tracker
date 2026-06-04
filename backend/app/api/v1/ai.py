from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.core.responses import APIResponse
from app.schemas.ai import AIRecommendationsResponse
from app.services.ai_recommendations import AIRecommendationsService

router = APIRouter()


@router.post("/recommendations", response_model=APIResponse[AIRecommendationsResponse])
async def generate_recommendations(
    user: CurrentUser,
    db: DbSession,
    month: str = Query(
        ...,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="Месяц в формате YYYY-MM",
    ),
) -> APIResponse[AIRecommendationsResponse]:
    service = AIRecommendationsService(db)
    content = await service.generate(user.id, month)
    return APIResponse(
        data=AIRecommendationsResponse(month=month, content=content),
        message="Рекомендации сгенерированы",
    )
