import time
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import AppException

settings = get_settings()

BASE_URL = "https://api.finam.ru"
TOKEN_TTL_SECONDS = 13 * 60  # JWT действителен 15 минут — обновляем заранее


class FinamApiError(AppException):

    def __init__(self, message: str = "Finam Trade API unavailable") -> None:
        super().__init__(message=message, code="BROKER_UNAVAILABLE", status_code=502)


class _TokenCache:
    value: str | None = None
    expires_at: float = 0.0


_token_cache = _TokenCache()


class FinamTradeApiClient:
    """
    Thin REST client for Finam's Trade API: exchanges the long-lived secret
    token for a short-lived JWT (cached in-process) and issues GET requests.
    """

    def __init__(self) -> None:
        if not settings.finam_api_token:
            raise FinamApiError("FINAM_API_TOKEN is not configured")
        self._secret = settings.finam_api_token
        self._client = httpx.AsyncClient(base_url=BASE_URL, timeout=20.0)

    async def __aenter__(self) -> "FinamTradeApiClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self._client.aclose()

    async def _get_jwt(self) -> str:
        if _token_cache.value and _token_cache.expires_at > time.monotonic():
            return _token_cache.value
        try:
            resp = await self._client.post("/v1/sessions", json={"secret": self._secret})
        except httpx.HTTPError as exc:
            raise FinamApiError(f"Failed to reach Finam Trade API: {exc}") from exc
        if resp.status_code >= 400:
            raise FinamApiError(f"Finam auth failed with HTTP {resp.status_code}")
        token = resp.json().get("token")
        if not token:
            raise FinamApiError("Finam auth response has no token")
        _token_cache.value = token
        _token_cache.expires_at = time.monotonic() + TOKEN_TTL_SECONDS
        return token

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        token = await self._get_jwt()
        try:
            resp = await self._client.get(
                path, params=params, headers={"Authorization": f"Bearer {token}"}
            )
        except httpx.HTTPError as exc:
            raise FinamApiError(f"Failed to reach Finam Trade API: {exc}") from exc
        if resp.status_code == 401:
            _token_cache.value = None
            raise FinamApiError("Finam Trade API token expired")
        if resp.status_code >= 400:
            raise FinamApiError(f"Finam Trade API returned HTTP {resp.status_code}")
        return resp.json()
