"""Tests for AsyncVisorClient listing endpoints — focused on filter serialization."""

from __future__ import annotations

import httpx
import pytest
import respx

from visor._client import AsyncVisorClient
from visor.models._base import BBox, InventoryMode, SortOrder
from visor.models.facets import FacetsFilter
from visor.models.listings import ListingsFilter

API_BASE = "https://api.visor.vin/v1"

PAGINATION = {"limit": 50, "offset": 0, "total": 1, "next_offset": None}
LISTING_SUMMARY = {"id": "abc123", "vin": "4T1DAACKXTU765422"}
LISTINGS_PAGE = {"data": [LISTING_SUMMARY], "pagination": PAGINATION, "meta": {}}

DEALER_REF = {"dealer_id": "d1", "name": "Dealer", "city": "Austin", "state": "TX"}
VEHICLE_BUILD = {"year": 2022, "make": "Toyota", "model": "Camry"}
LISTING_DETAIL = {
    "id": "abc123",
    "vin": "4T1DAACKXTU765422",
    "status": "active",
    "inventory_type": "new",
    "dealer": DEALER_REF,
    "vehicle": {"vin": "4T1DAACKXTU765422", "status": "active", "build": VEHICLE_BUILD},
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


# ---------------------------------------------------------------------------
# Separator quirks (critical per CLAUDE.md)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_assembly_location_pipe_separated() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        f = ListingsFilter(assembly_location=["US", "MX"])
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_listings(f)
    url = str(route.calls[0].request.url)
    assert "assembly_location=US%7CMX" in url or "assembly_location=US|MX" in url


@pytest.mark.asyncio
async def test_exclude_assembly_location_plus_separated() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        f = ListingsFilter(exclude_assembly_location=["JP", "DE"])
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_listings(f)
    url = str(route.calls[0].request.url)
    assert (
        "exclude_assembly_location=JP%2BDE" in url
        or "exclude_assembly_location=JP+DE" in url
    )


@pytest.mark.asyncio
async def test_normal_list_field_comma_separated() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        f = ListingsFilter(drivetrain=["AWD", "FWD"])
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_listings(f)
    url = str(route.calls[0].request.url)
    assert "drivetrain=" in url
    assert "AWD" in url
    assert "FWD" in url


# ---------------------------------------------------------------------------
# Multi-value list serialization
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_multiple_makes_comma_joined_in_param() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        f = ListingsFilter(make=["Toyota", "Honda", "Ford"])
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_listings(f)
    params = route.calls[0].request.url.params
    assert params["make"] == "Toyota,Honda,Ford"


@pytest.mark.asyncio
async def test_year_integers_serialized_in_url() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        f = ListingsFilter(year=[2023, 2024, 2025])
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_listings(f)
    params = route.calls[0].request.url.params
    assert params["year"] == "2023,2024,2025"


# ---------------------------------------------------------------------------
# Geo filters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_postal_code_and_radius_in_url() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        f = ListingsFilter(postal_code="78701", radius=50.0)
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_listings(f)
    url = str(route.calls[0].request.url)
    assert "postal_code=78701" in url
    assert "radius=50.0" in url


@pytest.mark.asyncio
async def test_bbox_serialized_as_csv_west_south_east_north() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        f = ListingsFilter(bbox=BBox(west=-97.0, south=30.0, east=-96.0, north=31.0))
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_listings(f)
    url = str(route.calls[0].request.url)
    assert "bbox=" in url
    assert "-97.0" in url
    assert "30.0" in url
    assert "31.0" in url


# ---------------------------------------------------------------------------
# Range filters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_min_max_price_in_url() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        f = ListingsFilter(min_price=20000, max_price=50000)
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_listings(f)
    url = str(route.calls[0].request.url)
    assert "min_price=20000" in url
    assert "max_price=50000" in url


@pytest.mark.asyncio
async def test_min_max_mileage_in_url() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        f = ListingsFilter(min_mileage=0, max_mileage=30000)
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_listings(f)
    url = str(route.calls[0].request.url)
    assert "min_mileage=0" in url
    assert "max_mileage=30000" in url


# ---------------------------------------------------------------------------
# Sort and fields projection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sort_param_serialized_in_url() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        f = ListingsFilter(sort=SortOrder.PRICE_DESC)
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_listings(f)
    url = str(route.calls[0].request.url)
    assert "sort=" in url
    assert "-price" in url


@pytest.mark.asyncio
async def test_fields_projection_serialized_in_url() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        f = ListingsFilter(fields=["id", "vin", "price"])
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_listings(f)
    url = str(route.calls[0].request.url)
    assert "fields=" in url
    assert "price" in url


# ---------------------------------------------------------------------------
# Inventory status / sold filters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sold_inventory_with_sold_within_days() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        f = ListingsFilter(
            inventory_status=InventoryMode.SOLD,
            sold_within_days=30,
        )
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_listings(f)
    url = str(route.calls[0].request.url)
    assert "inventory_status=sold" in url
    assert "sold_within_days=30" in url


@pytest.mark.asyncio
async def test_active_inventory_status_omitted_from_url() -> None:
    """Default inventory_status=active is omitted to keep URLs clean."""
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/listings").mock(
            return_value=httpx.Response(200, json=LISTINGS_PAGE)
        )
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_listings(ListingsFilter())
    url = str(route.calls[0].request.url)
    assert "inventory_status" not in url


# ---------------------------------------------------------------------------
# get_listing — include presence/absence
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_listing_no_include_omits_param() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/listings/abc123").mock(
            return_value=httpx.Response(200, json={"data": LISTING_DETAIL})
        )
        async with AsyncVisorClient(api_key="test") as client:
            await client.get_listing("abc123")
    url = str(route.calls[0].request.url)
    assert "include" not in url


# ---------------------------------------------------------------------------
# lookup_vin — include presence/absence
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lookup_vin_no_include_omits_param() -> None:
    vin = "4T1DAACKXTU765422"
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get(f"/vins/{vin}").mock(
            return_value=httpx.Response(200, json={"data": VIN_DETAIL})
        )
        async with AsyncVisorClient(api_key="test") as client:
            await client.lookup_vin(vin)
    url = str(route.calls[0].request.url)
    assert "include" not in url


# ---------------------------------------------------------------------------
# filter_facets — facets-specific params
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_filter_facets_facet_value_limit_in_url() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/facets").mock(
            return_value=httpx.Response(200, json=FACETS_RESPONSE)
        )
        f = FacetsFilter(facets=["make"], facet_value_limit=10)
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_facets(f)
    url = str(route.calls[0].request.url)
    assert "facet_value_limit=10" in url


@pytest.mark.asyncio
async def test_filter_facets_combined_listing_and_facet_params() -> None:
    """FacetsFilter inherits ListingsFilterBase — listing filters pass through."""
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/facets").mock(
            return_value=httpx.Response(200, json=FACETS_RESPONSE)
        )
        f = FacetsFilter(facets=["make"], make=["Toyota"], state=["TX"])
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_facets(f)
    url = str(route.calls[0].request.url)
    assert "facets=" in url
    assert "make=Toyota" in url
    assert "state=TX" in url


@pytest.mark.asyncio
async def test_filter_facets_multiple_facet_names_in_url() -> None:
    with respx.mock(base_url=API_BASE) as mock:
        route = mock.get("/facets").mock(
            return_value=httpx.Response(200, json=FACETS_RESPONSE)
        )
        f = FacetsFilter(facets=["make", "model", "year"])
        async with AsyncVisorClient(api_key="test") as client:
            await client.filter_facets(f)
    params = route.calls[0].request.url.params
    assert params["facets"] == "make,model,year"
