from typing import Any


class AppException(Exception):

    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(AppException):

    def __init__(self, message: str = "Resource not found", code: str = "NOT_FOUND") -> None:
        super().__init__(message=message, code=code, status_code=404)


class UnauthorizedError(AppException):

    def __init__(self, message: str = "Unauthorized", code: str = "UNAUTHORIZED") -> None:
        super().__init__(message=message, code=code, status_code=401)


class ForbiddenError(AppException):

    def __init__(self, message: str = "Forbidden", code: str = "FORBIDDEN") -> None:
        super().__init__(message=message, code=code, status_code=403)


class ConflictError(AppException):

    def __init__(self, message: str = "Conflict", code: str = "CONFLICT") -> None:
        super().__init__(message=message, code=code, status_code=409)


class ValidationError(AppException):

    def __init__(self, message: str = "Validation error", code: str = "VALIDATION_ERROR") -> None:
        super().__init__(message=message, code=code, status_code=422)


class BudgetExceededError(AppException):

    def __init__(self, message: str = "Budget exceeded") -> None:
        super().__init__(message=message, code="BUDGET_EXCEEDED", status_code=400)
