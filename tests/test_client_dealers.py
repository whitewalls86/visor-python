"""Tests for AsyncVisorClient dealer endpoints — focused on filter serialization."""

from __future__ import annotations

import httpx
import pytest
import respx

from visor._client import AsyncVisorClient
from visor.models.dealers import DealerFilter
from visor.models.listings import ListingsFilter

API_BASE = "https://api.visor.vin/v1"

PAGINATION = {"limit": 50, "offset": 0, "total": 1, "next_offset": None}
LISTING_SUMMARY = {"id": "abc123", "vin": "4T1DAACKXTU765422"}
LISTINGS_PAGE = {"data": [LISTING_SUMMARY], "pagination": PAGINATION, "meta": {}}

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


# ---------------------------------------------------------------------------
# DealerFilter default
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_dealers_default_sends_limit_and_offset() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/dealers").mock(
            return_value=httpx.Response(200, json=DEALERS_PAGE)
        )
        async with AsyncVisorClient(api_key="test") as client:
            await client.search_dealers()
    url = str(route.calls[0].request.url)
    assert "limit=50" in url
    assert "offset=0" in url


# ---------------------------------------------------------------------------
# DealerFilter param serialization
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_dealers_dealer_id_comma_joined() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/dealers").mock(
            return_value=httpx.Response(200, json=DEALERS_PAGE)
        )
        f = DealerFilter(dealer_id=["d1", "d2", "d3"])
        async with AsyncVisorClient(api_key="test") as client:
            await client.search_dealers(f)
    params = route.calls[0].request.url.params
    assert params["dealer_id"] == "d1,d2,d3"


@pytest.mark.asyncio
async def test_search_dealers_country_filter() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/dealers").mock(
            return_value=httpx.Response(200, json=DEALERS_PAGE)
        )
        f = DealerFilter(country="CA")
        async with AsyncVisorClient(api_key="test") as client:
            await client.search_dealers(f)
    url = str(route.calls[0].request.url)
    assert "country=CA" in url


@pytest.mark.asyncio
async def test_search_dealers_type_franchise() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/dealers").mock(
            return_value=httpx.Response(200, json=DEALERS_PAGE)
        )
        f = DealerFilter(type="franchise")
        async with AsyncVisorClient(api_key="test") as client:
            await client.search_dealers(f)
    url = str(route.calls[0].request.url)
    assert "type=franchise" in url


@pytest.mark.asyncio
async def test_search_dealers_type_independent() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/dealers").mock(
            return_value=httpx.Response(200, json=DEALERS_PAGE)
        )
        f = DealerFilter(type="independent")
        async with AsyncVisorClient(api_key="test") as client:
            await client.search_dealers(f)
    url = str(route.calls[0].request.url)
    assert "type=independent" in url


@pytest.mark.asyncio
async def test_search_dealers_q_text_search() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/dealers").mock(
            return_value=httpx.Response(200, json=DEALERS_PAGE)
        )
        f = DealerFilter(q="autonation")
        async with AsyncVisorClient(api_key="test") as client:
            await client.search_dealers(f)
    url = str(route.calls[0].request.url)
    assert "q=autonation" in url


@pytest.mark.asyncio
async def test_search_dealers_make_comma_joined() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/dealers").mock(
            return_value=httpx.Response(200, json=DEALERS_PAGE)
        )
        f = DealerFilter(make=["Toyota", "Honda"])
        async with AsyncVisorClient(api_key="test") as client:
            await client.search_dealers(f)
    params = route.calls[0].request.url.params
    assert params["make"] == "Toyota,Honda"


@pytest.mark.asyncio
async def test_search_dealers_state_comma_joined() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/dealers").mock(
            return_value=httpx.Response(200, json=DEALERS_PAGE)
        )
        f = DealerFilter(state=["TX", "CA", "NY"])
        async with AsyncVisorClient(api_key="test") as client:
            await client.search_dealers(f)
    params = route.calls[0].request.url.params
    assert params["state"] == "TX,CA,NY"


@pytest.mark.asyncio
async def test_search_dealers_pagination_params() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/dealers").mock(
            return_value=httpx.Response(200, json=DEALERS_PAGE)
        )
        f = DealerFilter(limit=10, offset=20)
        async with AsyncVisorClient(api_key="test") as client:
            await client.search_dealers(f)
    url = str(route.calls[0].request.url)
    assert "limit=10" in url
    assert "offset=20" in url


# ---------------------------------------------------------------------------
# dealer_inventory
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dealer_inventory_default_filter_sends_limit() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/dealers/d1/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        async with AsyncVisorClient(api_key="test") as client:
            await client.dealer_inventory("d1")
    url = str(route.calls[0].request.url)
    assert "limit=50" in url


@pytest.mark.asyncio
async def test_dealer_inventory_combined_make_year_price_filter() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/dealers/d1/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        f = ListingsFilter(make=["Toyota"], year=[2024, 2025], max_price=45000)
        async with AsyncVisorClient(api_key="test") as client:
            await client.dealer_inventory("d1", f)
    url = str(route.calls[0].request.url)
    assert "make=Toyota" in url
    assert "year=" in url
    assert "max_price=45000" in url


@pytest.mark.asyncio
async def test_dealer_inventory_routes_to_correct_dealer() -> None:
    """Different dealer IDs produce different request paths."""
    with respx.mock(base_url=API_BASE) as mock:
        route_a = mock.get("/dealers/alpha/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        route_b = mock.get("/dealers/beta/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        async with AsyncVisorClient(api_key="test") as client:
            await client.dealer_inventory("alpha")
            await client.dealer_inventory("beta")
    assert route_a.called
    assert route_b.called


@pytest.mark.asyncio
async def test_dealer_inventory_with_none_uses_default_filter() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/dealers/d1/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        async with AsyncVisorClient(api_key="test") as client:
            await client.dealer_inventory("d1", None)
    url = str(route.calls[0].request.url)
    assert "limit=50" in url
