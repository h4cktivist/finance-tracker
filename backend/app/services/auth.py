import json
import secrets
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictError, UnauthorizedError, ValidationError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    get_refresh_token_expiry,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.audit import AuditService

settings = get_settings()
RESET_TOKEN_TTL_SECONDS = 3600


class AuthService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.token_repo = RefreshTokenRepository(session)
        self.audit = AuditService(session)

    async def register(self, data: RegisterRequest, ip: str | None = None) -> User:
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ConflictError("Email already registered", code="EMAIL_EXISTS")
        user = User(email=data.email.lower(), hashed_password=hash_password(data.password))
        await self.user_repo.create(user)
        await self.audit.log("register", "user", user_id=user.id, entity_id=user.id, ip_address=ip)
        return user

    async def login(self, data: LoginRequest, ip: str | None = None) -> TokenResponse:
        user = await self.user_repo.get_by_email(data.email.lower())
        if user is None or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("Account is inactive")
        tokens = await self._issue_tokens(user)
        await self.audit.log("login", "user", user_id=user.id, entity_id=user.id, ip_address=ip)
        return tokens

    async def refresh(self, refresh_token: str, ip: str | None = None) -> TokenResponse:
        token_hash = hash_refresh_token(refresh_token)
        stored = await self.token_repo.get_by_hash(token_hash)
        if stored is None:
            raise UnauthorizedError("Invalid refresh token")
        user = await self.user_repo.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("User not found")
        await self.token_repo.revoke(stored)
        tokens = await self._issue_tokens(user)
        await self.audit.log("refresh", "user", user_id=user.id, entity_id=user.id, ip_address=ip)
        return tokens

    async def logout(self, refresh_token: str, ip: str | None = None) -> None:
        token_hash = hash_refresh_token(refresh_token)
        stored = await self.token_repo.get_by_hash(token_hash)
        if stored:
            await self.token_repo.revoke(stored)
            await self.audit.log(
                "logout", "user", user_id=stored.user_id, entity_id=stored.user_id, ip_address=ip
            )

    async def reset_password(
        self, email: str, new_password: str, reset_token: str, ip: str | None = None
    ) -> None:
        if not reset_token:
            raise ValidationError("Reset token is required")
        client = aioredis.from_url(settings.redis_url)
        try:
            key = f"reset:{reset_token}"
            stored = await client.get(key)
            if not stored:
                raise ValidationError("Invalid or expired reset token")
            payload = json.loads(stored)
            token_user_id = UUID(payload["user_id"])
        finally:
            await client.aclose()
        user = await self.user_repo.get_by_id(token_user_id)
        if user is None or user.email != email.lower():
            raise ValidationError("Invalid or expired reset token")
        user.hashed_password = hash_password(new_password)
        await self.session.flush()
        client = aioredis.from_url(settings.redis_url)
        try:
            await client.delete(key)
        finally:
            await client.aclose()
        await self.token_repo.revoke_all_for_user(user.id)
        await self.audit.log(
            "password_reset", "user", user_id=user.id, entity_id=user.id, ip_address=ip
        )

    async def request_password_reset(self, email: str) -> str | None:
        user = await self.user_repo.get_by_email(email.lower())
        if user is None:
            return None
        token = secrets.token_urlsafe(32)
        client = aioredis.from_url(settings.redis_url)
        try:
            await client.setex(
                f"reset:{token}", RESET_TOKEN_TTL_SECONDS, json.dumps({"user_id": str(user.id)})
            )
        finally:
            await client.aclose()
        if settings.debug:
            return token
        return None

    async def _issue_tokens(self, user: User) -> TokenResponse:
        access = create_access_token(user.id)
        refresh = generate_refresh_token()
        token_record = RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh),
            expires_at=get_refresh_token_expiry(),
        )
        await self.token_repo.create(token_record)
        return TokenResponse(access_token=access, refresh_token=refresh)
