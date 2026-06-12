from datetime import datetime
from email.utils import parsedate_to_datetime

import httpx

from visor.exceptions import (
    AuthError,
    ForbiddenError,
    NotFoundError,
    PaymentRequiredError,
    RateLimitError,
    ValidationError,
    VisorAPIError,
    VisorTransportError,
)

DEFAULT_BASE_URL = "https://api.visor.vin/v1"


def _parse_retry_after(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
        return max(0, int((retry_at - datetime.now(retry_at.tzinfo)).total_seconds()))


def _handle_response(response: httpx.Response) -> dict:  # type: ignore[type-arg]
    if response.is_success:
        return response.json()  # type: ignore[no-any-return]

    try:
        body = response.json()
        error_code = body.get("error", {}).get("code", "unknown_error")
        message = body.get("error", {}).get("message", response.text)
    except Exception:
        error_code = "unknown_error"
        message = response.text

    match response.status_code:
        case 400:
            raise ValidationError(400, error_code, message)
        case 401:
            raise AuthError(401, error_code, message)
        case 402:
            raise PaymentRequiredError(402, error_code, message)
        case 403:
            raise ForbiddenError(403, error_code, message)
        case 404:
            raise NotFoundError(404, error_code, message)
        case 429:
            retry_after = _parse_retry_after(response.headers.get("Retry-After"))
            raise RateLimitError(429, error_code, message, retry_after=retry_after)
        case _:
            raise VisorAPIError(response.status_code, error_code, message)


class AsyncVisorTransport:
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    async def get(self, path: str, params: dict[str, str] | None = None) -> dict:  # type: ignore[type-arg]
        try:
            response = await self._client.get(path, params=params or {})
        except httpx.RequestError as e:
            raise VisorTransportError(f"Request failed: {e}") from e
        return _handle_response(response)

    async def aclose(self) -> None:
        await self._client.aclose()


class SyncVisorTransport:
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    def get(self, path: str, params: dict[str, str] | None = None) -> dict:  # type: ignore[type-arg]
        try:
            response = self._client.get(path, params=params or {})
        except httpx.RequestError as e:
            raise VisorTransportError(f"Request failed: {e}") from e
        return _handle_response(response)

    def close(self) -> None:
        self._client.close()
