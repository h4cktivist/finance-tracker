from datetime import datetime

from pydantic import BaseModel, Field

from app.models.category import CategoryType


class CategoryCreate(BaseModel):
    name: str = Field(max_length=255)
    type: CategoryType
    parent_category_id: str | None = None
    color: str | None = Field(default=None, max_length=20)
    icon: str | None = Field(default=None, max_length=50)
    is_essential: bool = True


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    color: str | None = None
    icon: str | None = None
    is_essential: bool | None = None
    parent_category_id: str | None = None


class CategoryResponse(BaseModel):
    id: str
    user_id: str
    name: str
    type: CategoryType
    parent_category_id: str | None
    color: str | None
    icon: str | None
    is_essential: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class CategoryTreeNode(CategoryResponse):
    children: list["CategoryTreeNode"] = []


CategoryTreeNode.model_rebuild()
