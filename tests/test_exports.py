"""Smoke-test that all public symbols are importable from the visor package root."""

import visor

EXPECTED_EXPORTS = {
    # clients
    "AsyncVisorClient",
    "VisorClient",
    # pagination
    "paginate_listings",
    "paginate_dealers",
    "iter_listings",
    "iter_dealers",
    # exceptions
    "VisorError",
    "VisorAPIError",
    "VisorTransportError",
    "AuthError",
    "ForbiddenError",
    "NotFoundError",
    "ValidationError",
    "PaymentRequiredError",
    "RateLimitError",
    # filter / request models
    "ListingsFilter",
    "FacetsFilter",
    "DealerFilter",
    "BBox",
    # listing response models
    "ListingsPage",
    "ListingSummary",
    "ListingDetail",
    "ListingSnapshot",
    # dealer response models
    "DealersPage",
    "DealerSummary",
    "DealerDetail",
    "DealerAddress",
    # other response models
    "VinDetail",
    "UsageSummary",
    "UsageRecord",
    "UsageTotals",
    "UsageMeta",
    "FacetsResponse",
    "FacetsData",
    "FacetBucket",
    # shared models
    "Pagination",
    "DealerRef",
    "VehicleBuild",
    "VehicleRecord",
    "VehicleOption",
}

PRIVATE_TRANSPORT = {"AsyncVisorTransport", "SyncVisorTransport"}


def test_all_contains_expected():
    missing = EXPECTED_EXPORTS - set(visor.__all__)
    assert not missing, f"Missing from __all__: {sorted(missing)}"


def test_symbols_importable():
    missing = [name for name in EXPECTED_EXPORTS if not hasattr(visor, name)]
    assert not missing, f"Not importable from visor: {sorted(missing)}"


def test_transport_internals_not_exported():
    leaked = PRIVATE_TRANSPORT & set(visor.__all__)
    assert not leaked, f"Internal transport classes in __all__: {sorted(leaked)}"


def test_readme_imports():
    from visor import AsyncVisorClient, ListingsFilter, VisorClient, iter_listings

    assert AsyncVisorClient is visor.AsyncVisorClient
    assert VisorClient is visor.VisorClient
    assert ListingsFilter is visor.ListingsFilter
    assert iter_listings is visor.iter_listings
