from datetime import date

import pytest

from visor.models._base import BBox, InventoryMode, ListingsFilterBase
from visor.models.facets import FacetsFilter
from visor.models.listings import ListingsFilter

# ---------------------------------------------------------------------------
# Separator correctness
# ---------------------------------------------------------------------------


def test_assembly_location_pipe_separator() -> None:
    f = ListingsFilter(assembly_location=["Erlangen, Germany", "Georgetown, KY"])
    params = f.to_params()
    assert params["assembly_location"] == "Erlangen, Germany|Georgetown, KY"


def test_exclude_assembly_location_plus_separator() -> None:
    f = ListingsFilter(exclude_assembly_location=["Georgetown, KY"])
    params = f.to_params()
    assert params["exclude_assembly_location"] == "Georgetown, KY"


def test_standard_list_comma_separator() -> None:
    f = ListingsFilter(make=["Toyota", "Honda"])
    assert f.to_params()["make"] == "Toyota,Honda"


# ---------------------------------------------------------------------------
# Geo validation
# ---------------------------------------------------------------------------


def test_radius_requires_geo_anchor() -> None:
    with pytest.raises(ValueError, match="radius requires"):
        ListingsFilter(radius=50)


def test_radius_with_postal_code_ok() -> None:
    f = ListingsFilter(radius=50, postal_code="77001")
    assert f.to_params()["radius"] == "50.0"


def test_radius_with_latlon_ok() -> None:
    f = ListingsFilter(radius=50, latitude=29.7, longitude=-95.4)
    assert "radius" in f.to_params()


def test_bbox_and_radius_mutually_exclusive() -> None:
    with pytest.raises(ValueError, match="mutually exclusive"):
        ListingsFilter(
            postal_code="77001",
            radius=50,
            bbox=BBox(-97.5, 29.5, -95.0, 30.5),
        )


def test_bbox_serializes_correctly() -> None:
    f = ListingsFilter(bbox=BBox(-97.5, 29.5, -95.0, 30.5))
    assert f.to_params()["bbox"] == "-97.5,29.5,-95.0,30.5"


# ---------------------------------------------------------------------------
# Inventory mode validation
# ---------------------------------------------------------------------------


def test_sold_within_days_requires_sold_mode() -> None:
    with pytest.raises(ValueError):
        ListingsFilter(sold_within_days=30)


def test_snapshot_date_requires_active_mode() -> None:
    with pytest.raises(ValueError):
        ListingsFilter(
            inventory_status=InventoryMode.SOLD,
            snapshot_date=date(2026, 1, 1),
        )


def test_sold_within_days_and_snapshot_mutually_exclusive() -> None:
    with pytest.raises(ValueError):
        ListingsFilter(
            inventory_status=InventoryMode.SOLD,
            sold_within_days=30,
            snapshot_date=date(2026, 1, 1),
        )


# ---------------------------------------------------------------------------
# Projection validation
# ---------------------------------------------------------------------------


def test_unknown_field_rejected() -> None:
    with pytest.raises(ValueError, match="unknown fields"):
        ListingsFilter(fields=["not_a_real_field"])


def test_fields_projection_serializes() -> None:
    f = ListingsFilter(fields=["id", "vin", "price"])
    assert f.to_params()["fields"] == "id,vin,price"


# ---------------------------------------------------------------------------
# Limit cap
# ---------------------------------------------------------------------------


def test_limit_max_100() -> None:
    with pytest.raises(ValueError):
        ListingsFilter(limit=101)


# ---------------------------------------------------------------------------
# None values are dropped
# ---------------------------------------------------------------------------


def test_none_values_not_in_params() -> None:
    f = ListingsFilter()
    params = f.to_params()
    assert "make" not in params
    assert "model" not in params


# ---------------------------------------------------------------------------
# Facets validation
# ---------------------------------------------------------------------------


def test_unknown_facet_rejected() -> None:
    with pytest.raises(ValueError, match="unknown facets"):
        FacetsFilter(facets=["not_a_facet"])


def test_valid_facets_accepted() -> None:
    f = FacetsFilter(facets=["make", "model", "price"])
    params = f.to_params()
    assert params["facets"] == "make,model,price"


# ---------------------------------------------------------------------------
# snapshot_date serialization
# ---------------------------------------------------------------------------


def test_snapshot_date_serializes() -> None:
    f = ListingsFilter(snapshot_date=date(2025, 6, 15))
    assert f.to_params()["snapshot_date"] == "2025-06-15"


# ---------------------------------------------------------------------------
# include serialization
# ---------------------------------------------------------------------------


def test_include_serializes() -> None:
    f = ListingsFilter(include=["price_history", "options"])
    assert f.to_params()["include"] == "price_history,options"


# ---------------------------------------------------------------------------
# Empty list filters are omitted from query params
# ---------------------------------------------------------------------------


def test_empty_list_omitted_from_params() -> None:
    # Empty lists (not None) are falsy and skipped by the comma/pipe helpers,
    # so they are omitted from the serialized query string.
    f = ListingsFilter(make=[])
    assert "make" not in f.to_params()


# ---------------------------------------------------------------------------
# ListingsFilterBase is accessible directly (used by downstream callers)
# ---------------------------------------------------------------------------


def test_listings_filter_base_importable() -> None:
    assert issubclass(ListingsFilter, ListingsFilterBase)
