from datetime import datetime

from pydantic import BaseModel, Field


class TagCreate(BaseModel):
    name: str = Field(max_length=100)
    color: str | None = Field(default=None, max_length=20)


class TagUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    color: str | None = None


class TagResponse(BaseModel):
    id: str
    user_id: str
    name: str
    color: str | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
