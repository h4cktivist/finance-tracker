from pydantic import BaseModel, Field


class AIRecommendationsResponse(BaseModel):
    month: str = Field(description="Период в формате YYYY-MM")
    content: str = Field(description="Текст рекомендаций (markdown)")
