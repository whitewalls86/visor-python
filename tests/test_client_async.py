"""Tests for AsyncVisorClient — all HTTP mocked via respx."""

from __future__ import annotations

from datetime import date

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
    VisorTransportError,
)
from visor.models.dealers import DealerDetail, DealerFilter, DealersPage
from visor.models.facets import FacetsFilter, FacetsResponse
from visor.models.listings import ListingDetail, ListingsFilter, ListingsPage
from visor.models.usage import UsageSummary
from visor.models.vins import VinDetail

API_BASE = "https://api.visor.vin/v1"

# ---------------------------------------------------------------------------
# Shared fixture data
# ---------------------------------------------------------------------------

PAGINATION = {"limit": 50, "offset": 0, "total": 1, "next_offset": None}

LISTING_SUMMARY = {
    "id": "abc123",
    "vin": "4T1DAACKXTU765422",
    "year": 2026,
    "make": "Toyota",
    "model": "Camry",
    "price": 35000,
    "miles": 0,
    "inventory_type": "new",
}

LISTINGS_PAGE = {"data": [LISTING_SUMMARY], "pagination": PAGINATION, "meta": {}}

DEALER_REF = {
    "dealer_id": "d1",
    "name": "Test Dealer",
    "city": "Austin",
    "state": "TX",
}

VEHICLE_BUILD = {
    "year": 2022,
    "make": "Toyota",
    "model": "Camry",
}

LISTING_DETAIL = {
    "id": "abc123",
    "vin": "4T1DAACKXTU765422",
    "status": "active",
    "inventory_type": "new",
    "dealer": DEALER_REF,
    "vehicle": {
        "vin": "4T1DAACKXTU765422",
        "status": "active",
        "build": VEHICLE_BUILD,
    },
}

VIN_DETAIL = {
    "vin": "4T1DAACKXTU765422",
    "status": "active",
    "build": VEHICLE_BUILD,
    "latest_listing": None,
}

FACETS_RESPONSE = {
    "data": {
        "total": 100,
        "facets": {"make": [{"value": "Toyota", "count": 50}]},
        "range_facets": {},
        "stats": {},
    },
    "meta": {
        "facets": ["make"],
        "metric": "count",
        "sort": "-count",
        "minimum_metric_count": 1,
    },
}

DEALER_SUMMARY = {
    "dealer_id": "d1",
    "name": "Test Dealer",
    "city": "Austin",
    "state": "TX",
    "country": "US",
    "type": "franchise",
    "listing_count": 42,
}

DEALERS_PAGE = {"data": [DEALER_SUMMARY], "pagination": PAGINATION, "meta": {}}

DEALER_DETAIL = {**DEALER_SUMMARY, "phone": None, "address": None}

USAGE_SUMMARY = {
    "data": [
        {
            "date": "2026-01-01",
            "metering_class": "listings",
            "requests": 100,
            "charged_micros": 1000,
        }
    ],
    "totals": {"requests": 100, "charged_micros": 1000},
    "meta": {
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
        "interval": "day",
        "currency": "USD",
        "source": "billing",
        "freshness": "realtime",
    },
}

ERROR_BODY = {"error": {"code": "some_error", "message": "msg"}}


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------


def test_constructor_explicit_api_key() -> None:
    with respx.mock(base_url=API_BASE):
        client = AsyncVisorClient(api_key="mykey")
        assert client._transport._client.headers["authorization"] == "Bearer mykey"


def test_constructor_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VISOR_API_KEY", "envkey")
    client = AsyncVisorClient()
    assert client._transport._client.headers["authorization"] == "Bearer envkey"


def test_constructor_raises_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VISOR_API_KEY", raising=False)
    with pytest.raises(ValueError, match="api_key is required"):
        AsyncVisorClient()


def test_constructor_explicit_key_overrides_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VISOR_API_KEY", "envkey")
    client = AsyncVisorClient(api_key="explicitkey")
    assert client._transport._client.headers["authorization"] == "Bearer explicitkey"


# ---------------------------------------------------------------------------
# Authorization header flows through transport
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auth_header_sent() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        async with AsyncVisorClient(api_key="secret-key") as client:
            await client.filter_listings()
        assert route.calls[0].request.headers["authorization"] == "Bearer secret-key"


# ---------------------------------------------------------------------------
# filter_listings
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_filter_listings_returns_listings_page() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        mock.get("/listings").mock(return_value=httpx.Response(200, json=LISTINGS_PAGE))
        async with AsyncVisorClient(api_key="test") as client:
            result = await client.filter_listings()
    assert isinstance(result, ListingsPage)
    assert len(result.data) == 1
    assert result.data[0].vin == "4T1DAACKXTU765422"


@pytest.mark.asyncio
async def test_filter_listings_passes_filter_params() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        f = ListingsFilter(make=["Toyota"], state=["TX"], max_price=40000)
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_listings(f)
    url = str(route.calls[0].request.url)
    assert "make=Toyota" in url
    assert "state=TX" in url
    assert "max_price=40000" in url


@pytest.mark.asyncio
async def test_filter_listings_default_filter_used_when_none() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_listings(None)
    # default filter always sends limit and offset
    url = str(route.calls[0].request.url)
    assert "limit=50" in url


# ---------------------------------------------------------------------------
# get_listing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_listing_hits_correct_path() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/listings/abc123").mock(
            return_value=httpx.Response(200, json={"data": LISTING_DETAIL})
        )
        async with AsyncVisorClient(api_key="test") as client:
            result = await client.get_listing("abc123")
    assert route.called
    assert isinstance(result, ListingDetail)
    assert result.id == "abc123"


@pytest.mark.asyncio
async def test_get_listing_include_serializes() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/listings/abc123").mock(
            return_value=httpx.Response(200, json={"data": LISTING_DETAIL})
        )
        async with AsyncVisorClient(api_key="test") as client:
            await client.get_listing("abc123", include=["price_history", "options"])
    url = str(route.calls[0].request.url)
    assert (
        "include=price_history%2Coptions" in url
        or "include=price_history,options" in url
    )


# ---------------------------------------------------------------------------
# lookup_vin
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lookup_vin_hits_correct_path() -> None:
    vin = "4T1DAACKXTU765422"
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get(f"/vins/{vin}").mock(
            return_value=httpx.Response(200, json={"data": VIN_DETAIL})
        )
        async with AsyncVisorClient(api_key="test") as client:
            result = await client.lookup_vin(vin)
    assert route.called
    assert isinstance(result, VinDetail)
    assert result.vin == vin


@pytest.mark.asyncio
async def test_lookup_vin_include_serializes() -> None:
    vin = "4T1DAACKXTU765422"
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get(f"/vins/{vin}").mock(
            return_value=httpx.Response(200, json={"data": VIN_DETAIL})
        )
        async with AsyncVisorClient(api_key="test") as client:
            await client.lookup_vin(vin, include=["price_history", "options"])
    url = str(route.calls[0].request.url)
    assert "include=" in url
    assert "price_history" in url
    assert "options" in url


# ---------------------------------------------------------------------------
# filter_facets
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_filter_facets_hits_correct_path() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/facets").mock(
            return_value=httpx.Response(200, json=FACETS_RESPONSE)
        )
        f = FacetsFilter(facets=["make"])
        async with AsyncVisorClient(api_key="test") as client:
            result = await client.filter_facets(f)
    assert route.called
    assert isinstance(result, FacetsResponse)


@pytest.mark.asyncio
async def test_filter_facets_passes_params() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/facets").mock(
            return_value=httpx.Response(200, json=FACETS_RESPONSE)
        )
        f = FacetsFilter(facets=["make", "model"])
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_facets(f)
    url = str(route.calls[0].request.url)
    assert "facets=" in url
    assert "make" in url


# ---------------------------------------------------------------------------
# search_dealers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_dealers_hits_correct_path() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/dealers").mock(
            return_value=httpx.Response(200, json=DEALERS_PAGE)
        )
        async with AsyncVisorClient(api_key="test") as client:
            result = await client.search_dealers()
    assert route.called
    assert isinstance(result, DealersPage)
    assert len(result.data) == 1


@pytest.mark.asyncio
async def test_search_dealers_filter_params() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/dealers").mock(
            return_value=httpx.Response(200, json=DEALERS_PAGE)
        )
        f = DealerFilter(state=["TX"], make=["Toyota"])
        async with AsyncVisorClient(api_key="test") as client:
            await client.search_dealers(f)
    url = str(route.calls[0].request.url)
    assert "state=TX" in url
    assert "make=Toyota" in url


# ---------------------------------------------------------------------------
# get_dealer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_dealer_hits_correct_path() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/dealers/d1").mock(
            return_value=httpx.Response(200, json={"data": DEALER_DETAIL})
        )
        async with AsyncVisorClient(api_key="test") as client:
            result = await client.get_dealer("d1")
    assert route.called
    assert isinstance(result, DealerDetail)
    assert result.dealer_id == "d1"


# ---------------------------------------------------------------------------
# dealer_inventory
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dealer_inventory_hits_correct_path() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/dealers/d1/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        async with AsyncVisorClient(api_key="test") as client:
            result = await client.dealer_inventory("d1")
    assert route.called
    assert isinstance(result, ListingsPage)


@pytest.mark.asyncio
async def test_dealer_inventory_passes_filter_params() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/dealers/d1/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        f = ListingsFilter(make=["Toyota"])
        async with AsyncVisorClient(api_key="test") as client:
            await client.dealer_inventory("d1", f)
    url = str(route.calls[0].request.url)
    assert "make=Toyota" in url


# ---------------------------------------------------------------------------
# get_usage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_usage_hits_correct_path() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/usage").mock(
            return_value=httpx.Response(200, json=USAGE_SUMMARY)
        )
        async with AsyncVisorClient(api_key="test") as client:
            result = await client.get_usage()
    assert route.called
    assert isinstance(result, UsageSummary)


@pytest.mark.asyncio
async def test_get_usage_params_serialize_dates() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/usage").mock(
            return_value=httpx.Response(200, json=USAGE_SUMMARY)
        )
        async with AsyncVisorClient(api_key="test") as client:
            await client.get_usage(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31),
            )
    url = str(route.calls[0].request.url)
    assert "start_date=2026-01-01" in url
    assert "end_date=2026-01-31" in url


@pytest.mark.asyncio
async def test_get_usage_metering_class_serializes() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/usage").mock(
            return_value=httpx.Response(200, json=USAGE_SUMMARY)
        )
        async with AsyncVisorClient(api_key="test") as client:
            await client.get_usage(metering_class=["listings", "vins"])
    url = str(route.calls[0].request.url)
    assert "metering_class=" in url
    assert "listings" in url
    assert "vins" in url


# ---------------------------------------------------------------------------
# Error propagation
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
        (500, VisorAPIError),
    ],
)
async def test_error_dispatch(status: int, exc_class: type[VisorAPIError]) -> None:
    with respx.mock(base_url=API_BASE) as mock:
        mock.get("/listings").mock(return_value=httpx.Response(status, json=ERROR_BODY))
        async with AsyncVisorClient(api_key="test") as client:
            with pytest.raises(exc_class):
                await client.filter_listings()


@pytest.mark.asyncio
async def test_rate_limit_carries_retry_after() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        mock.get("/listings").mock(
            return_value=httpx.Response(
                429,
                headers={"Retry-After": "30"},
                json={"error": {"code": "rate_limited", "message": "slow down"}},
            )
        )
        async with AsyncVisorClient(api_key="test") as client:
            with pytest.raises(RateLimitError) as exc_info:
                await client.filter_listings()
    assert exc_info.value.retry_after == 30


@pytest.mark.asyncio
async def test_transport_error_propagates() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        mock.get("/listings").mock(side_effect=httpx.ConnectError("refused"))
        async with AsyncVisorClient(api_key="test") as client:
            with pytest.raises(VisorTransportError):
                await client.filter_listings()


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_context_manager_closes_transport() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        mock.get("/listings").mock(return_value=httpx.Response(200, json=LISTINGS_PAGE))
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_listings()
        # After __aexit__, the underlying httpx client should be closed
        assert client._transport._client.is_closed
