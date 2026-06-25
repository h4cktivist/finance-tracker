import time
from typing import Any

import httpx

from app.core.exceptions import AppException

BASE_URL = "https://api.finam.ru"
TOKEN_TTL_SECONDS = 13 * 60  # JWT действителен 15 минут — обновляем заранее


class FinamApiError(AppException):

    def __init__(self, message: str = "Finam Trade API unavailable") -> None:
        super().__init__(message=message, code="BROKER_UNAVAILABLE", status_code=502)


# Каждый пользователь приносит свой секретный токен (хранится у него в браузере,
# а не на сервере), поэтому JWT кэшируется отдельно для каждого секрета.
_jwt_cache: dict[str, tuple[str, float]] = {}


class FinamTradeApiClient:
    """
    Thin REST client for Finam's Trade API: exchanges the user-supplied secret
    token for a short-lived JWT (cached in-process per secret) and issues GET requests.
    """

    def __init__(self, secret: str) -> None:
        if not secret:
            raise FinamApiError("Finam API secret is empty")
        self._secret = secret
        self._client = httpx.AsyncClient(base_url=BASE_URL, timeout=20.0)

    async def __aenter__(self) -> "FinamTradeApiClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self._client.aclose()

    async def _get_jwt(self) -> str:
        cached = _jwt_cache.get(self._secret)
        if cached and cached[1] > time.monotonic():
            return cached[0]
        try:
            resp = await self._client.post("/v1/sessions", json={"secret": self._secret})
        except httpx.HTTPError as exc:
            raise FinamApiError(f"Failed to reach Finam Trade API: {exc}") from exc
        if resp.status_code >= 400:
            raise FinamApiError(f"Finam auth failed with HTTP {resp.status_code}")
        token = resp.json().get("token")
        if not token:
            raise FinamApiError("Finam auth response has no token")
        _jwt_cache[self._secret] = (token, time.monotonic() + TOKEN_TTL_SECONDS)
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
            _jwt_cache.pop(self._secret, None)
            raise FinamApiError("Finam Trade API token expired")
        if resp.status_code >= 400:
            raise FinamApiError(f"Finam Trade API returned HTTP {resp.status_code}")
        return resp.json()
