from datetime import datetime, timedelta, timezone
from email.utils import format_datetime as email_format_datetime

import httpx
import pytest
import respx

from visor._transport import DEFAULT_BASE_URL, AsyncVisorTransport, SyncVisorTransport
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

API_KEY = "test-key"
SUCCESS_BODY = {"data": {"id": "abc"}}
ERROR_BODY = {"error": {"code": "some_error", "message": "something went wrong"}}


# ---------------------------------------------------------------------------
# Async transport
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_auth_header_sent():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=SUCCESS_BODY)
        )
        transport = AsyncVisorTransport(api_key=API_KEY)
        await transport.get("/listings")
        await transport.aclose()

    assert route.called
    auth = route.calls[0].request.headers["Authorization"]
    assert auth == f"Bearer {API_KEY}"


@pytest.mark.asyncio
async def test_async_base_url_path_composition():
    custom_base = "https://api.visor.vin/v1"
    with respx.mock(base_url=custom_base) as mock:
        route = mock.get("/vins/ABC123").mock(
            return_value=httpx.Response(200, json=SUCCESS_BODY)
        )
        transport = AsyncVisorTransport(api_key=API_KEY, base_url=custom_base)
        await transport.get("/vins/ABC123")
        await transport.aclose()

    assert route.called


@pytest.mark.asyncio
async def test_async_query_params_passed():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=SUCCESS_BODY)
        )
        transport = AsyncVisorTransport(api_key=API_KEY)
        await transport.get("/listings", params={"make": "Toyota", "state": "TX"})
        await transport.aclose()

    url = str(route.calls[0].request.url)
    assert "make=Toyota" in url
    assert "state=TX" in url


@pytest.mark.asyncio
async def test_async_success_returns_json():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(return_value=httpx.Response(200, json=SUCCESS_BODY))
        transport = AsyncVisorTransport(api_key=API_KEY)
        result = await transport.get("/listings")
        await transport.aclose()

    assert result == SUCCESS_BODY


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code, exc_class",
    [
        (400, ValidationError),
        (401, AuthError),
        (402, PaymentRequiredError),
        (403, ForbiddenError),
        (404, NotFoundError),
        (429, RateLimitError),
        (500, VisorAPIError),
    ],
)
async def test_async_error_status_raises(status_code: int, exc_class: type) -> None:
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(status_code, json=ERROR_BODY)
        )
        transport = AsyncVisorTransport(api_key=API_KEY)
        with pytest.raises(exc_class):
            await transport.get("/listings")
        await transport.aclose()


@pytest.mark.asyncio
async def test_async_rate_limit_carries_retry_after():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(
                429,
                headers={"Retry-After": "60"},
                json=ERROR_BODY,
            )
        )
        transport = AsyncVisorTransport(api_key=API_KEY)
        with pytest.raises(RateLimitError) as exc_info:
            await transport.get("/listings")
        await transport.aclose()

    assert exc_info.value.retry_after == 60


@pytest.mark.asyncio
async def test_async_rate_limit_retry_after_none_when_missing():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(return_value=httpx.Response(429, json=ERROR_BODY))
        transport = AsyncVisorTransport(api_key=API_KEY)
        with pytest.raises(RateLimitError) as exc_info:
            await transport.get("/listings")
        await transport.aclose()

    assert exc_info.value.retry_after is None


@pytest.mark.asyncio
async def test_async_non_json_error_body_unknown_error():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(
                503,
                content=b"<html>Service Unavailable</html>",
                headers={"Content-Type": "text/html"},
            )
        )
        transport = AsyncVisorTransport(api_key=API_KEY)
        with pytest.raises(VisorAPIError) as exc_info:
            await transport.get("/listings")
        await transport.aclose()

    assert exc_info.value.error_code == "unknown_error"
    assert "Service Unavailable" in exc_info.value.message


@pytest.mark.asyncio
async def test_async_request_error_raises_transport_error():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(side_effect=httpx.ConnectError("connection refused"))
        transport = AsyncVisorTransport(api_key=API_KEY)
        with pytest.raises(VisorTransportError):
            await transport.get("/listings")
        await transport.aclose()


@pytest.mark.asyncio
async def test_async_malformed_error_envelope_unknown_error():
    """{"error": "oops"} — error is a string, not a dict; must not crash."""
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(500, json={"error": "oops"})
        )
        transport = AsyncVisorTransport(api_key=API_KEY)
        with pytest.raises(VisorAPIError) as exc_info:
            await transport.get("/listings")
        await transport.aclose()

    assert exc_info.value.error_code == "unknown_error"


# ---------------------------------------------------------------------------
# Sync transport
# ---------------------------------------------------------------------------


def test_sync_auth_header_sent():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=SUCCESS_BODY)
        )
        transport = SyncVisorTransport(api_key=API_KEY)
        transport.get("/listings")
        transport.close()

    assert route.called
    auth = route.calls[0].request.headers["Authorization"]
    assert auth == f"Bearer {API_KEY}"


def test_sync_query_params_passed():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=SUCCESS_BODY)
        )
        transport = SyncVisorTransport(api_key=API_KEY)
        transport.get("/listings", params={"make": "Ford", "state": "CA"})
        transport.close()

    url = str(route.calls[0].request.url)
    assert "make=Ford" in url
    assert "state=CA" in url


def test_sync_success_returns_json():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(return_value=httpx.Response(200, json=SUCCESS_BODY))
        transport = SyncVisorTransport(api_key=API_KEY)
        result = transport.get("/listings")
        transport.close()

    assert result == SUCCESS_BODY


@pytest.mark.parametrize(
    "status_code, exc_class",
    [
        (400, ValidationError),
        (401, AuthError),
        (402, PaymentRequiredError),
        (403, ForbiddenError),
        (404, NotFoundError),
        (429, RateLimitError),
        (500, VisorAPIError),
    ],
)
def test_sync_error_status_raises(status_code: int, exc_class: type) -> None:
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(status_code, json=ERROR_BODY)
        )
        transport = SyncVisorTransport(api_key=API_KEY)
        with pytest.raises(exc_class):
            transport.get("/listings")
        transport.close()


def test_sync_rate_limit_carries_retry_after():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(
                429,
                headers={"Retry-After": "45"},
                json=ERROR_BODY,
            )
        )
        transport = SyncVisorTransport(api_key=API_KEY)
        with pytest.raises(RateLimitError) as exc_info:
            transport.get("/listings")
        transport.close()

    assert exc_info.value.retry_after == 45


def test_sync_non_json_error_body_unknown_error():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(
                503,
                content=b"<html>Service Unavailable</html>",
                headers={"Content-Type": "text/html"},
            )
        )
        transport = SyncVisorTransport(api_key=API_KEY)
        with pytest.raises(VisorAPIError) as exc_info:
            transport.get("/listings")
        transport.close()

    assert exc_info.value.error_code == "unknown_error"
    assert "Service Unavailable" in exc_info.value.message


def test_sync_request_error_raises_transport_error():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(side_effect=httpx.ConnectError("connection refused"))
        transport = SyncVisorTransport(api_key=API_KEY)
        with pytest.raises(VisorTransportError):
            transport.get("/listings")
        transport.close()


# ---------------------------------------------------------------------------
# Fallback messages for empty 401 / 403 bodies
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "status_code, exc_class", [(401, AuthError), (403, ForbiddenError)]
)
def test_sync_empty_body_fallback_message(status_code: int, exc_class: type) -> None:
    """When the API returns 401/403 with no body, a useful default message is set."""
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(status_code, content=b"")
        )
        transport = SyncVisorTransport(api_key=API_KEY)
        with pytest.raises(exc_class) as exc_info:
            transport.get("/listings")
        transport.close()

    assert exc_info.value.message


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code, exc_class", [(401, AuthError), (403, ForbiddenError)]
)
async def test_async_empty_body_fallback_message(
    status_code: int, exc_class: type
) -> None:
    """When the API returns 401/403 with no body, a useful default message is set."""
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(status_code, content=b"")
        )
        transport = AsyncVisorTransport(api_key=API_KEY)
        with pytest.raises(exc_class) as exc_info:
            await transport.get("/listings")
        await transport.aclose()

    assert exc_info.value.message


# ---------------------------------------------------------------------------
# Malformed JSON on 2xx raises VisorTransportError
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_malformed_success_json_raises_transport_error():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(
                200,
                content=b"not-valid-json{{{",
                headers={"Content-Type": "application/json"},
            )
        )
        transport = AsyncVisorTransport(api_key=API_KEY)
        with pytest.raises(VisorTransportError):
            await transport.get("/listings")
        await transport.aclose()


def test_sync_malformed_success_json_raises_transport_error():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(
                200,
                content=b"not-valid-json{{{",
                headers={"Content-Type": "application/json"},
            )
        )
        transport = SyncVisorTransport(api_key=API_KEY)
        with pytest.raises(VisorTransportError):
            transport.get("/listings")
        transport.close()


def test_sync_non_object_success_json_raises_transport_error():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(return_value=httpx.Response(200, json=[1, 2, 3]))
        transport = SyncVisorTransport(api_key=API_KEY)
        with pytest.raises(VisorTransportError):
            transport.get("/listings")
        transport.close()


@pytest.mark.asyncio
async def test_async_non_object_success_json_raises_transport_error():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(return_value=httpx.Response(200, json=[1, 2, 3]))
        transport = AsyncVisorTransport(api_key=API_KEY)
        with pytest.raises(VisorTransportError):
            await transport.get("/listings")
        await transport.aclose()


# ---------------------------------------------------------------------------
# Retry-After: HTTP-date and invalid-value coverage
# ---------------------------------------------------------------------------


def _future_http_date(seconds_ahead: int = 120) -> str:
    """Return a valid RFC 7231 HTTP-date string for a moment in the future."""
    future = datetime.now(timezone.utc) + timedelta(seconds=seconds_ahead)
    return email_format_datetime(future, usegmt=True)


def test_sync_rate_limit_retry_after_http_date():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(
                429,
                headers={"Retry-After": _future_http_date(120)},
                json=ERROR_BODY,
            )
        )
        transport = SyncVisorTransport(api_key=API_KEY)
        with pytest.raises(RateLimitError) as exc_info:
            transport.get("/listings")
        transport.close()

    assert isinstance(exc_info.value.retry_after, int)
    assert exc_info.value.retry_after >= 0


def test_sync_rate_limit_retry_after_invalid_value():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(
                429,
                headers={"Retry-After": "not-a-number-or-date"},
                json=ERROR_BODY,
            )
        )
        transport = SyncVisorTransport(api_key=API_KEY)
        with pytest.raises(RateLimitError) as exc_info:
            transport.get("/listings")
        transport.close()

    assert exc_info.value.retry_after is None


@pytest.mark.asyncio
async def test_async_rate_limit_retry_after_http_date():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(
                429,
                headers={"Retry-After": _future_http_date(120)},
                json=ERROR_BODY,
            )
        )
        transport = AsyncVisorTransport(api_key=API_KEY)
        with pytest.raises(RateLimitError) as exc_info:
            await transport.get("/listings")
        await transport.aclose()

    assert isinstance(exc_info.value.retry_after, int)
    assert exc_info.value.retry_after >= 0


@pytest.mark.asyncio
async def test_async_rate_limit_retry_after_invalid_value():
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(
                429,
                headers={"Retry-After": "not-a-number-or-date"},
                json=ERROR_BODY,
            )
        )
        transport = AsyncVisorTransport(api_key=API_KEY)
        with pytest.raises(RateLimitError) as exc_info:
            await transport.get("/listings")
        await transport.aclose()

    assert exc_info.value.retry_after is None
