"""Response model parsing tests against API doc example shapes."""

from datetime import date

import pytest
from pydantic import ValidationError

from visor.models._base import (
    DealerRef,
    VehicleBuild,
    VehicleRecord,
)
from visor.models.dealers import (
    DealerAddress,
    DealerDetail,
    DealerFilter,
    DealersPage,
    DealerSummary,
)
from visor.models.facets import (
    FacetsData,
    FacetsResponse,
)
from visor.models.listings import (
    ListingDetail,
    ListingSnapshot,
    ListingsPage,
    ListingSummary,
)
from visor.models.usage import UsageSummary
from visor.models.vins import VinDetail

# ---------------------------------------------------------------------------
# ListingSummary
# ---------------------------------------------------------------------------


def test_listing_summary_minimal() -> None:
    data = {"id": "abc123", "vin": "4T1DAACKXTU765422"}
    ls = ListingSummary.model_validate(data)
    assert ls.id == "abc123"
    assert ls.vin == "4T1DAACKXTU765422"
    assert ls.photo_urls == []
    assert ls.features == []
    assert ls.options_packages == []
    assert ls.price_history == []
    assert ls.options == []


def test_listing_summary_full() -> None:
    data = {
        "id": "0043554b54709f18a7bcf42f23e5e6ef",
        "vin": "4T1DAACKXTU765422",
        "year": 2026,
        "make": "Toyota",
        "model": "Camry",
        "trim": "SE",
        "price": 35236,
        "miles": 0,
        "status": "active",
        "inventory_status": "active",
        "inventory_type": "new",
        "dealer_id": "16ed7612-0ffd-4e1e-88db-174f8dd57c54",
        "dealer_name": "North Hollywood Toyota",
        "city": "North Hollywood",
        "state": "CA",
        "vdp_url": "https://example.com/vin",
        "photo_urls": ["https://example.com/img1.jpg"],
        "features": ["Backup Camera"],
        "options_packages": ["Technology Package"],
        "price_history": [{"date": "2026-01-01", "price": 36000}],
        "options": [{"code": "OPT1", "name": "Sunroof", "msrp": 1200}],
        "unknown_future_field": "ignored",
    }
    ls = ListingSummary.model_validate(data)
    assert ls.year == 2026
    assert ls.make == "Toyota"
    assert ls.price == 35236
    assert len(ls.photo_urls) == 1
    assert len(ls.price_history) == 1
    assert ls.price_history[0].price == 36000
    assert ls.options[0].code == "OPT1"


def test_listing_summary_extra_fields_ignored() -> None:
    data = {"id": "x", "vin": "y", "beta_field_not_in_spec": True}
    ls = ListingSummary.model_validate(data)
    assert ls.id == "x"


# ---------------------------------------------------------------------------
# ListingDetail
# ---------------------------------------------------------------------------


DEALER_REF_DATA = {
    "dealer_id": "16ed7612-0ffd-4e1e-88db-174f8dd57c54",
    "name": "North Hollywood Toyota",
    "city": "North Hollywood",
    "state": "CA",
}

VEHICLE_RECORD_DATA = {
    "vin": "4T1DAACKXTU765422",
    "status": "active",
    "build": {
        "year": 2026,
        "make": "Toyota",
        "model": "Camry",
        "trim": "SE",
        "combined_msrp": 37500,
    },
}


def test_listing_detail_parses() -> None:
    data = {
        "id": "abc",
        "vin": "4T1DAACKXTU765422",
        "status": "active",
        "inventory_type": "new",
        "price": 35236,
        "dealer": DEALER_REF_DATA,
        "vehicle": VEHICLE_RECORD_DATA,
    }
    ld = ListingDetail.model_validate(data)
    assert ld.id == "abc"
    assert ld.vehicle.build.combined_msrp == 37500
    assert ld.dealer.name == "North Hollywood Toyota"
    assert ld.photo_urls == []
    assert ld.price_history == []


def test_listing_detail_vehicle_uses_vehicle_record() -> None:
    data = {
        "id": "x",
        "vin": "VIN1",
        "status": "active",
        "inventory_type": "used",
        "dealer": DEALER_REF_DATA,
        "vehicle": VEHICLE_RECORD_DATA,
    }
    ld = ListingDetail.model_validate(data)
    assert isinstance(ld.vehicle, VehicleRecord)
    assert isinstance(ld.vehicle.build, VehicleBuild)


# ---------------------------------------------------------------------------
# ListingsPage
# ---------------------------------------------------------------------------


def test_listings_page_parses() -> None:
    data = {
        "data": [{"id": "a", "vin": "V1"}, {"id": "b", "vin": "V2"}],
        "pagination": {"limit": 50, "offset": 0, "total": 2, "next_offset": None},
        "meta": {},
    }
    page = ListingsPage.model_validate(data)
    assert len(page.data) == 2
    assert page.pagination.total == 2
    assert page.pagination.next_offset is None


def test_listings_page_next_offset() -> None:
    data = {
        "data": [],
        "pagination": {"limit": 2, "offset": 0, "total": 100, "next_offset": 2},
        "meta": {"query_ms": 42},
    }
    page = ListingsPage.model_validate(data)
    assert page.pagination.next_offset == 2


# ---------------------------------------------------------------------------
# ListingSnapshot (embedded in VinDetail)
# ---------------------------------------------------------------------------


def test_listing_snapshot_parses() -> None:
    data = {
        "id": "snap1",
        "inventory_type": "new",
        "price": 40000,
        "dealer": DEALER_REF_DATA,
    }
    snap = ListingSnapshot.model_validate(data)
    assert snap.id == "snap1"
    assert snap.price == 40000
    assert isinstance(snap.dealer, DealerRef)


# ---------------------------------------------------------------------------
# VinDetail — latest_listing uses ListingSnapshot
# ---------------------------------------------------------------------------


def test_vin_detail_no_listing() -> None:
    data = {
        "vin": "4T1DAACKXTU765422",
        "status": "active",
        "build": {"year": 2026, "make": "Toyota", "model": "Camry"},
    }
    vd = VinDetail.model_validate(data)
    assert vd.vin == "4T1DAACKXTU765422"
    assert vd.latest_listing is None
    assert isinstance(vd.build, VehicleBuild)


def test_vin_detail_with_listing() -> None:
    data = {
        "vin": "4T1DAACKXTU765422",
        "status": "active",
        "build": {"year": 2026, "make": "Toyota", "model": "Camry"},
        "latest_listing": {
            "id": "snap1",
            "inventory_type": "new",
            "dealer": DEALER_REF_DATA,
        },
    }
    vd = VinDetail.model_validate(data)
    assert isinstance(vd.latest_listing, ListingSnapshot)
    assert vd.latest_listing.id == "snap1"


# ---------------------------------------------------------------------------
# FacetsResponse
# ---------------------------------------------------------------------------


def test_facets_response_parses() -> None:
    data = {
        "data": {
            "total": 5000,
            "facets": {
                "make": [
                    {"value": "Toyota", "count": 1200},
                    {"value": "Honda", "count": 800},
                ]
            },
            "range_facets": {
                "price": {
                    "buckets": [{"min": 0.0, "max": 20000.0, "count": 300}],
                    "interval": 5000.0,
                    "min": 0.0,
                    "max": 100000.0,
                }
            },
            "stats": {},
        },
        "meta": {
            "facets": ["make", "price"],
            "metric": "count",
            "sort": "-count",
            "minimum_metric_count": 1,
        },
    }
    resp = FacetsResponse.model_validate(data)
    assert resp.data.total == 5000
    assert len(resp.data.facets["make"]) == 2
    assert resp.data.facets["make"][0].value == "Toyota"
    assert resp.data.facets["make"][0].count == 1200
    assert "price" in resp.data.range_facets
    assert resp.data.range_facets["price"].interval == 5000.0
    assert resp.meta.sort == "-count"


def test_facets_data_defaults() -> None:
    fd = FacetsData.model_validate({"total": 0})
    assert fd.facets == {}
    assert fd.range_facets == {}
    assert fd.stats == {}


# ---------------------------------------------------------------------------
# DealerSummary / DealerDetail / DealersPage
# ---------------------------------------------------------------------------

DEALER_SUMMARY_DATA = {
    "dealer_id": "16ed7612-0ffd-4e1e-88db-174f8dd57c54",
    "name": "North Hollywood Toyota",
    "city": "North Hollywood",
    "state": "CA",
    "country": "US",
    "type": "franchise",
    "listing_count": 142,
    "makes": ["Toyota"],
    "latitude": 34.17,
    "longitude": -118.38,
}


def test_dealer_summary_parses() -> None:
    ds = DealerSummary.model_validate(DEALER_SUMMARY_DATA)
    assert ds.dealer_id == "16ed7612-0ffd-4e1e-88db-174f8dd57c54"
    assert ds.listing_count == 142
    assert ds.makes == ["Toyota"]


def test_dealer_summary_makes_default() -> None:
    data = {**DEALER_SUMMARY_DATA, "makes": []}
    ds = DealerSummary.model_validate(data)
    assert ds.makes == []


def test_dealer_detail_with_address() -> None:
    data = {
        **DEALER_SUMMARY_DATA,
        "phone": "555-0100",
        "address": {
            "line1": "12345 Magnolia Blvd",
            "city": "North Hollywood",
            "state": "CA",
            "country": "US",
        },
    }
    dd = DealerDetail.model_validate(data)
    assert dd.phone == "555-0100"
    assert isinstance(dd.address, DealerAddress)
    assert dd.address.line1 == "12345 Magnolia Blvd"


def test_dealer_detail_no_address() -> None:
    dd = DealerDetail.model_validate(DEALER_SUMMARY_DATA)
    assert dd.address is None
    assert dd.phone is None


def test_dealers_page_parses() -> None:
    data = {
        "data": [DEALER_SUMMARY_DATA],
        "pagination": {"limit": 50, "offset": 0, "total": 1, "next_offset": None},
        "meta": {},
    }
    page = DealersPage.model_validate(data)
    assert len(page.data) == 1
    assert page.data[0].name == "North Hollywood Toyota"


# ---------------------------------------------------------------------------
# DealerFilter.to_params
# ---------------------------------------------------------------------------


def test_dealer_filter_defaults() -> None:
    f = DealerFilter()
    params = f.to_params()
    assert params["limit"] == "50"
    assert params["offset"] == "0"
    assert "dealer_id" not in params


def test_dealer_filter_with_values() -> None:
    f = DealerFilter(
        limit=10,
        offset=20,
        state=["CA", "TX"],
        make=["Toyota"],
        type="franchise",
        q="toyota",
    )
    params = f.to_params()
    assert params["limit"] == "10"
    assert params["offset"] == "20"
    assert params["state"] == "CA,TX"
    assert params["make"] == "Toyota"
    assert params["type"] == "franchise"
    assert params["q"] == "toyota"


def test_dealer_filter_extra_fields_rejected() -> None:
    with pytest.raises(ValidationError):
        DealerFilter(unknown_param="value")  # type: ignore[call-arg]


def test_dealer_filter_limit_max_100() -> None:
    with pytest.raises(ValidationError, match="limit maximum is 100"):
        DealerFilter(limit=101)


def test_dealer_filter_dealer_id_max_100() -> None:
    with pytest.raises(ValidationError, match="dealer_id maximum is 100"):
        DealerFilter(dealer_id=[str(i) for i in range(101)])


def test_dealer_filter_limit_100_ok() -> None:
    f = DealerFilter(limit=100)
    assert f.to_params()["limit"] == "100"


def test_dealer_filter_dealer_id_100_ok() -> None:
    ids = [str(i) for i in range(100)]
    f = DealerFilter(dealer_id=ids)
    assert len(f.dealer_id) == 100  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# FacetsFilter validators
# ---------------------------------------------------------------------------


from visor.models.facets import FacetsFilter  # noqa: E402


def test_facets_filter_value_limit_max_100() -> None:
    with pytest.raises(ValidationError, match="facet_value_limit maximum is 100"):
        FacetsFilter(facets=["make"], facet_value_limit=101)


def test_facets_filter_value_limit_100_ok() -> None:
    f = FacetsFilter(facets=["make"], facet_value_limit=100)
    assert f.to_params()["facet_value_limit"] == "100"


def test_facets_filter_metric_requires_one_categorical_facet() -> None:
    with pytest.raises(ValidationError, match="exactly one categorical facet"):
        FacetsFilter(facets=["make", "model"], metric="price.p95")


def test_facets_filter_metric_with_range_only_rejected() -> None:
    with pytest.raises(ValidationError, match="exactly one categorical facet"):
        FacetsFilter(facets=["price"], metric="price.p95")


def test_facets_filter_metric_with_one_categorical_ok() -> None:
    f = FacetsFilter(facets=["make", "price"], metric="price.p95")
    params = f.to_params()
    assert params["metric"] == "price.p95"
    assert "make" in params["facets"]


def test_facets_filter_no_metric_allows_multiple_categoricals() -> None:
    f = FacetsFilter(facets=["make", "model", "state"])
    assert f.metric is None


# ---------------------------------------------------------------------------
# UsageSummary
# ---------------------------------------------------------------------------


def test_usage_summary_parses() -> None:
    data = {
        "data": [
            {
                "date": "2026-06-01",
                "metering_class": "listings",
                "requests": 150,
                "charged_micros": 1500000,
            }
        ],
        "totals": {"requests": 150, "charged_micros": 1500000},
        "meta": {
            "start_date": "2026-06-01",
            "end_date": "2026-06-30",
            "interval": "day",
            "currency": "USD",
            "source": "api",
            "freshness": "realtime",
        },
    }
    us = UsageSummary.model_validate(data)
    assert len(us.data) == 1
    assert us.data[0].date == date(2026, 6, 1)
    assert us.data[0].metering_class == "listings"
    assert us.totals.requests == 150
    assert us.totals.charged_micros == 1500000
    assert us.meta.interval == "day"
    assert us.meta.currency == "USD"
    assert us.meta.start_date == date(2026, 6, 1)


def test_usage_summary_extra_fields_ignored() -> None:
    data = {
        "data": [],
        "totals": {"requests": 0, "charged_micros": 0},
        "meta": {
            "start_date": "2026-06-01",
            "end_date": "2026-06-30",
            "interval": "day",
            "currency": "USD",
            "source": "api",
            "freshness": "realtime",
            "future_field": "ignored",
        },
    }
    us = UsageSummary.model_validate(data)
    assert us.meta.interval == "day"
