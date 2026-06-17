import pytest

from visor import ListingsFilter, ValidationError, VisorClient
from visor.models.listings import ListingDetail, ListingsPage

pytestmark = [pytest.mark.integration, pytest.mark.release_gate]


def test_filter_listings_default(client: VisorClient) -> None:
    page = client.filter_listings()
    assert isinstance(page, ListingsPage)
    assert len(page.data) > 0
    assert page.pagination.total > 0
    assert page.pagination.limit == 50
    assert page.pagination.offset == 0


def test_filter_listings_by_make_and_state(client: VisorClient) -> None:
    page = client.filter_listings(
        ListingsFilter(make=["Toyota"], state=["TX"], limit=5)
    )
    assert len(page.data) > 0
    for listing in page.data:
        if listing.make:
            assert listing.make == "Toyota"
        if listing.state:
            assert listing.state == "TX"


def test_filter_listings_geo_postal_code(client: VisorClient) -> None:
    try:
        page = client.filter_listings(
            ListingsFilter(
                postal_code="77001",
                radius=50,
                limit=5,
                fields=["id", "vin", "distance_miles"],
            )
        )
    except ValidationError as exc:
        pytest.skip(
            f"Postal code unresolved by live API ({exc.error_code}) — skipping geo test"
        )
    if not page.data:
        pytest.skip("No listings near Houston 77001 — cannot validate geo response")
    distances = [lst.distance_miles for lst in page.data if lst.distance_miles]
    if not distances:
        pytest.skip(
            "No distance_miles populated in geo response — cannot validate range"
        )
    assert all(d <= 50 for d in distances)


def test_filter_listings_fields_projection(client: VisorClient) -> None:
    page = client.filter_listings(
        ListingsFilter(limit=3, fields=["id", "vin", "price", "make", "model"])
    )
    for listing in page.data:
        assert listing.id is not None
        assert listing.vin is not None
        assert listing.stock_number is None
        assert listing.vdp_url is None


def test_filter_listings_include_price_history(client: VisorClient) -> None:
    page = client.filter_listings(ListingsFilter(limit=3, include=["price_history"]))
    for listing in page.data:
        assert isinstance(listing.price_history, list)


def test_filter_listings_include_options(client: VisorClient) -> None:
    page = client.filter_listings(ListingsFilter(limit=3, include=["options"]))
    for listing in page.data:
        assert isinstance(listing.options, list)


def test_get_listing(client: VisorClient, sample_listing_id: str) -> None:
    listing = client.get_listing(sample_listing_id)
    assert isinstance(listing, ListingDetail)
    assert listing.id == sample_listing_id
    assert listing.vin is not None
    assert listing.dealer is not None
    assert listing.dealer.dealer_id is not None
    assert listing.vehicle is not None
    assert listing.vehicle.build.year is not None


def test_get_listing_with_price_history(
    client: VisorClient, sample_listing_id: str
) -> None:
    listing = client.get_listing(sample_listing_id, include=["price_history"])
    assert isinstance(listing.price_history, list)


def test_get_listing_with_options(client: VisorClient, sample_listing_id: str) -> None:
    listing = client.get_listing(sample_listing_id, include=["options"])
    assert isinstance(listing.vehicle.build.options, list)


# ---------------------------------------------------------------------------
# ListingSummary include-field raw-shape guards
#
# Background: ListingSummary.price_history and ListingSummary.options use
# list[...] with default_factory=list.  That type does NOT accept null — if
# the API ever sends null for these fields without include=, Pydantic will
# raise a ValidationError at parse time.
#
# We verified via live probe (2026-06-17) that the API omits both fields
# entirely from the raw JSON when include= is not passed.  Pydantic's
# default_factory=list kicks in, so listing.price_history == [] means
# "field was absent from response", not "requested and empty".
#
# These tests re-verify that invariant on every release-gate run.  If either
# assertion fails it means the API started sending null (model type is wrong)
# or [] (model type is technically fine but semantics become ambiguous —
# revisit whether to make the field Optional so callers can distinguish
# "not requested" from "requested but empty").
# ---------------------------------------------------------------------------

_SENTINEL = object()


def _check_include_field_raw(client: VisorClient, field: str) -> None:
    """Assert field is absent (not null, not []) in raw listings without include=."""
    raw = client._transport.get("/listings", {"limit": "5"})
    items: list[dict] = raw.get("data", [])
    assert items, "No listings in response"
    for item in items:
        val = item.get(field, _SENTINEL)
        assert val is _SENTINEL, (
            f"ListingSummary.{field} unexpectedly present in raw response "
            f"without include=: {val!r}. "
            f"If null: change type to list[...] | None. "
            f"If []: field is now always sent; consider Optional for caller clarity."
        )


@pytest.mark.integration
@pytest.mark.release_gate
def test_listing_summary_price_history_absent_without_include(
    client: VisorClient,
) -> None:
    """price_history must be absent from raw JSON when include= is not passed.

    Verified live 2026-06-17: API omits the key entirely; Pydantic default []
    applies.  Failure here means the API changed shape — re-evaluate the model.
    """
    _check_include_field_raw(client, "price_history")


@pytest.mark.integration
@pytest.mark.release_gate
def test_listing_summary_options_absent_without_include(client: VisorClient) -> None:
    """options must be absent from raw JSON when include=options is not passed.

    Verified live 2026-06-17: API omits the key entirely; Pydantic default []
    applies.  Failure here means the API changed shape — re-evaluate the model.
    """
    _check_include_field_raw(client, "options")
