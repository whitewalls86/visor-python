"""Tests for the exception hierarchy and dispatch behavior."""

from __future__ import annotations

import httpx
import pytest
import respx

from visor._client import AsyncVisorClient
from visor.exceptions import (
    AuthError,
    ForbiddenError,
    NotFoundError,
    PaymentRequiredError,
    RateLimitError,
    ValidationError,
    VisorAPIError,
    VisorError,
    VisorTransportError,
)

API_BASE = "https://api.visor.vin/v1"
LISTINGS_PAGE = {
    "data": [],
    "pagination": {"limit": 50, "offset": 0, "total": 0, "next_offset": None},
    "meta": {},
}
ERROR_BODY = {"error": {"code": "some_error", "message": "something went wrong"}}


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


def test_visor_api_error_is_visor_error() -> None:
    assert issubclass(VisorAPIError, VisorError)


def test_auth_error_is_visor_api_error() -> None:
    assert issubclass(AuthError, VisorAPIError)
    assert issubclass(AuthError, VisorError)


def test_forbidden_error_is_visor_api_error() -> None:
    assert issubclass(ForbiddenError, VisorAPIError)


def test_not_found_error_is_visor_api_error() -> None:
    assert issubclass(NotFoundError, VisorAPIError)


def test_validation_error_is_visor_api_error() -> None:
    assert issubclass(ValidationError, VisorAPIError)


def test_payment_required_error_is_visor_api_error() -> None:
    assert issubclass(PaymentRequiredError, VisorAPIError)


def test_rate_limit_error_is_visor_api_error() -> None:
    assert issubclass(RateLimitError, VisorAPIError)


def test_transport_error_is_visor_error() -> None:
    assert issubclass(VisorTransportError, VisorError)


def test_transport_error_is_not_api_error() -> None:
    assert not issubclass(VisorTransportError, VisorAPIError)


# ---------------------------------------------------------------------------
# VisorAPIError attributes and string format
# ---------------------------------------------------------------------------


def test_visor_api_error_attributes_stored() -> None:
    exc = VisorAPIError(404, "not_found", "Resource not found")
    assert exc.status_code == 404
    assert exc.error_code == "not_found"
    assert exc.message == "Resource not found"


def test_visor_api_error_str_contains_all_parts() -> None:
    exc = VisorAPIError(400, "validation_error", "bad param")
    s = str(exc)
    assert "400" in s
    assert "validation_error" in s
    assert "bad param" in s


def test_rate_limit_error_retry_after_stored() -> None:
    exc = RateLimitError(429, "rate_limited", "slow down", retry_after=60)
    assert exc.retry_after == 60
    assert exc.status_code == 429
    assert exc.error_code == "rate_limited"
    assert exc.message == "slow down"


def test_rate_limit_error_retry_after_defaults_to_none() -> None:
    exc = RateLimitError(429, "rate_limited", "slow down")
    assert exc.retry_after is None


# ---------------------------------------------------------------------------
# Exception dispatch through client — status codes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,exc_class",
    [
        (400, ValidationError),
        (401, AuthError),
        (402, PaymentRequiredError),
        (403, ForbiddenError),
        (404, NotFoundError),
        (429, RateLimitError),
    ],
)
async def test_mapped_status_dispatches_correct_subclass(
    status: int, exc_class: type[VisorAPIError]
) -> None:
    with respx.mock(base_url=API_BASE) as mock:
        mock.get("/listings").mock(return_value=httpx.Response(status, json=ERROR_BODY))
        async with AsyncVisorClient(api_key="test") as client:
            with pytest.raises(exc_class):
                await client.filter_listings()


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [500, 503])
async def test_unmapped_status_raises_base_visor_api_error(status: int) -> None:
    with respx.mock(base_url=API_BASE) as mock:
        mock.get("/listings").mock(return_value=httpx.Response(status, json=ERROR_BODY))
        async with AsyncVisorClient(api_key="test") as client:
            with pytest.raises(VisorAPIError) as exc_info:
                await client.filter_listings()
    assert type(exc_info.value) is VisorAPIError


# ---------------------------------------------------------------------------
# RateLimitError retry_after header parsing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rate_limit_retry_after_from_integer_header() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(
                429, headers={"Retry-After": "30"}, json=ERROR_BODY
            )
        )
        async with AsyncVisorClient(api_key="test") as client:
            with pytest.raises(RateLimitError) as exc_info:
                await client.filter_listings()
    assert exc_info.value.retry_after == 30


@pytest.mark.asyncio
async def test_rate_limit_retry_after_none_when_header_absent() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        mock.get("/listings").mock(return_value=httpx.Response(429, json=ERROR_BODY))
        async with AsyncVisorClient(api_key="test") as client:
            with pytest.raises(RateLimitError) as exc_info:
                await client.filter_listings()
    assert exc_info.value.retry_after is None


# ---------------------------------------------------------------------------
# Network-level failures → VisorTransportError
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connect_error_raises_transport_error() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        mock.get("/listings").mock(side_effect=httpx.ConnectError("refused"))
        async with AsyncVisorClient(api_key="test") as client:
            with pytest.raises(VisorTransportError):
                await client.filter_listings()


@pytest.mark.asyncio
async def test_timeout_raises_transport_error() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        mock.get("/listings").mock(side_effect=httpx.TimeoutException("timed out"))
        async with AsyncVisorClient(api_key="test") as client:
            with pytest.raises(VisorTransportError):
                await client.filter_listings()


# ---------------------------------------------------------------------------
# Malformed / missing error body edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_non_json_response_body_falls_back_to_unknown_error() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(
                502,
                content=b"<html>Bad Gateway</html>",
                headers={"Content-Type": "text/html"},
            )
        )
        async with AsyncVisorClient(api_key="test") as client:
            with pytest.raises(VisorAPIError) as exc_info:
                await client.filter_listings()
    assert exc_info.value.error_code == "unknown_error"
    assert "Bad Gateway" in exc_info.value.message


@pytest.mark.asyncio
async def test_error_body_missing_error_key_falls_back_to_unknown() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(500, json={"message": "internal error"})
        )
        async with AsyncVisorClient(api_key="test") as client:
            with pytest.raises(VisorAPIError) as exc_info:
                await client.filter_listings()
    assert exc_info.value.error_code == "unknown_error"


@pytest.mark.asyncio
async def test_error_body_with_string_error_field_falls_back_to_unknown() -> None:
    """{"error": "string"} — error is not a dict, must not crash."""
    with respx.mock(base_url=API_BASE) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(500, json={"error": "something broke"})
        )
        async with AsyncVisorClient(api_key="test") as client:
            with pytest.raises(VisorAPIError) as exc_info:
                await client.filter_listings()
    assert exc_info.value.error_code == "unknown_error"
