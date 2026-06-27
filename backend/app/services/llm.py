import httpx

from app.core.config import get_settings
from app.core.exceptions import AppException

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


async def call_openrouter(
    system: str,
    user_msg: str,
    *,
    temperature: float = 0.6,
    max_tokens: int = 2048,
) -> str:
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise AppException(
            message="Сервис ИИ не настроен (OPENROUTER_API_KEY)",
            code="AI_NOT_CONFIGURED",
            status_code=503,
        )

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://finance-tracker.local",
        "X-Title": "Finance Tracker",
    }
    body = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(OPENROUTER_URL, headers=headers, json=body)
    except httpx.TimeoutException as exc:
        raise AppException(
            message="Превышено время ожидания ответа от ИИ",
            code="AI_TIMEOUT",
            status_code=504,
        ) from exc
    except httpx.HTTPError as exc:
        raise AppException(
            message="Не удалось связаться с сервисом ИИ",
            code="AI_NETWORK_ERROR",
            status_code=502,
        ) from exc

    if response.status_code != 200:
        detail = response.text[:500]
        raise AppException(
            message="Сервис ИИ вернул ошибку",
            code="AI_PROVIDER_ERROR",
            status_code=502,
            details={"status": response.status_code, "body": detail},
        )

    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AppException(
            message="Некорректный ответ от сервиса ИИ",
            code="AI_INVALID_RESPONSE",
            status_code=502,
        ) from exc

    if not content or not str(content).strip():
        raise AppException(
            message="Сервис ИИ вернул пустой ответ",
            code="AI_EMPTY_RESPONSE",
            status_code=502,
        )
    return str(content).strip()
