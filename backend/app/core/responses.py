from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str = ""


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
