from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.config import get_settings
from app.core.deps import DbSession, get_client_ip
from app.core.exceptions import ValidationError
from app.core.limiter import limiter
from app.core.responses import APIResponse
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import AuthService

router = APIRouter()
settings = get_settings()


@router.post("/register", response_model=APIResponse[UserResponse])
@limiter.limit(settings.rate_limit_auth)
async def register(
    request: Request,
    data: RegisterRequest,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[UserResponse]:
    service = AuthService(db)
    user = await service.register(data, ip=ip)
    return APIResponse(
        data=UserResponse(
            id=str(user.id),
            email=user.email,
            is_active=user.is_active,
            is_verified=user.is_verified,
        ),
        message="Registration successful",
    )


@router.post("/login", response_model=APIResponse[TokenResponse])
@limiter.limit(settings.rate_limit_auth)
async def login(
    request: Request,
    data: LoginRequest,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[TokenResponse]:
    service = AuthService(db)
    tokens = await service.login(data, ip=ip)
    return APIResponse(data=tokens, message="Login successful")


@router.post("/refresh", response_model=APIResponse[TokenResponse])
@limiter.limit(settings.rate_limit_auth)
async def refresh(
    request: Request,
    data: RefreshRequest,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[TokenResponse]:
    service = AuthService(db)
    tokens = await service.refresh(data.refresh_token, ip=ip)
    return APIResponse(data=tokens)


@router.post("/logout", response_model=APIResponse[None])
@limiter.limit(settings.rate_limit_auth)
async def logout(
    request: Request,
    data: RefreshRequest,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[None]:
    service = AuthService(db)
    await service.logout(data.refresh_token, ip=ip)
    return APIResponse(message="Logged out")


@router.post("/reset-password", response_model=APIResponse[None])
@limiter.limit(settings.rate_limit_auth)
async def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    db: DbSession,
    ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> APIResponse[None]:
    service = AuthService(db)
    if data.new_password or data.reset_token:
        if not data.new_password or not data.reset_token:
            raise ValidationError("Both new_password and reset_token are required")
        await service.reset_password(data.email, data.new_password, data.reset_token, ip=ip)
        return APIResponse(message="Password reset successful")
    token = await service.request_password_reset(data.email)
    msg = "If the email exists, a reset link was sent"
    if token and settings.debug:
        return APIResponse(message=f"{msg}. Dev token: {token}")
    return APIResponse(message=msg)
