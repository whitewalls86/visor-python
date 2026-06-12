from datetime import date
from enum import Enum
from typing import Any, NamedTuple

from pydantic import BaseModel, ConfigDict, Field, model_validator


class VisorRequestModel(BaseModel):
    """Base for request/filter models. The API fails closed on unknown params."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class VisorResponseModel(BaseModel):
    """Base for API responses. Beta responses may add fields over time."""

    model_config = ConfigDict(extra="ignore")


# ---------------------------------------------------------------------------
# Shared response building blocks
# ---------------------------------------------------------------------------


class VehicleOption(VisorResponseModel):
    code: str
    name: str
    msrp: int | None = None


class VehicleBuild(VisorResponseModel):
    year: int
    make: str
    model: str
    trim: str | None = None
    version: str | None = None
    body_type: str | None = None
    drivetrain: str | None = None
    fuel_type: str | None = None
    powertrain_type: str | None = None
    transmission: str | None = None
    engine: str | None = None
    cylinders: int | None = None
    doors: int | None = None
    seating_capacity: int | None = None
    exterior_color: str | None = None
    interior_color: str | None = None
    base_exterior_color: str | None = None
    base_interior_color: str | None = None
    assembly_location: str | None = None
    assembly_country: str | None = None
    window_sticker_verified: bool = False
    base_msrp: int | None = None
    combined_msrp: int | None = None
    options: list[VehicleOption] = Field(default_factory=list)


class VehicleRecord(VisorResponseModel):
    """VIN-level wrapper as returned inside ListingDetail.vehicle."""

    vin: str
    status: str
    build: VehicleBuild


class PriceHistoryEntry(VisorResponseModel):
    date: date
    price: int


class DealerRef(VisorResponseModel):
    dealer_id: str
    name: str
    city: str
    state: str
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None


class Pagination(VisorResponseModel):
    limit: int
    offset: int
    total: int
    next_offset: int | None = None


class BBox(NamedTuple):
    """Bounding box for map-viewport filtering: west, south, east, north."""

    west: float
    south: float
    east: float
    north: float


# ---------------------------------------------------------------------------
# Filter enums
# ---------------------------------------------------------------------------


class InventoryMode(str, Enum):
    ACTIVE = "active"
    SOLD = "sold"


class SortOrder(str, Enum):
    DAYS_ON_MARKET = "days_on_market"
    DAYS_ON_MARKET_DESC = "-days_on_market"
    PRICE = "price"
    PRICE_DESC = "-price"
    MILES = "miles"
    MILES_DESC = "-miles"
    MSRP = "msrp"
    MSRP_DESC = "-msrp"
    DISCOUNT = "discount"
    DISCOUNT_DESC = "-discount"
    DISTANCE = "distance"


# ---------------------------------------------------------------------------
# ListingsFilterBase — shared by ListingsFilter and FacetsFilter
# ---------------------------------------------------------------------------


class ListingsFilterBase(VisorRequestModel):
    # Categorical filters (comma-separated on the wire)
    make: list[str] | None = None
    model: list[str] | None = None
    trim: list[str] | None = None
    year: list[int] | None = None
    state: list[str] | None = None
    dealer_id: list[str] | None = None
    dealer_type: list[str] | None = None
    availability_status: list[str] | None = None
    inventory_type: list[str] | None = None
    body_type: list[str] | None = None
    transmission: list[str] | None = None
    drivetrain: list[str] | None = None
    fuel_type: list[str] | None = None
    powertrain_type: list[str] | None = None
    engine: list[str] | None = None
    version: list[str] | None = None
    exterior_color: list[str] | None = None
    interior_color: list[str] | None = None
    base_exterior_color: list[str] | None = None
    base_interior_color: list[str] | None = None
    seating_capacity: list[int] | None = None
    cylinders: list[int] | None = None
    doors: list[int] | None = None
    options_packages: list[str] | None = None
    features: list[str] | None = None
    keywords: list[str] | None = None
    vin_pattern: list[str] | None = None

    # assembly_location uses PIPE separator (not comma)
    assembly_location: list[str] | None = None
    assembly_country: list[str] | None = None

    # Exclude counterparts (comma-separated, EXCEPT assembly_location uses "+")
    exclude_make: list[str] | None = None
    exclude_model: list[str] | None = None
    exclude_trim: list[str] | None = None
    exclude_year: list[int] | None = None
    exclude_state: list[str] | None = None
    exclude_inventory_type: list[str] | None = None
    exclude_body_type: list[str] | None = None
    exclude_transmission: list[str] | None = None
    exclude_drivetrain: list[str] | None = None
    exclude_version: list[str] | None = None
    exclude_engine: list[str] | None = None
    exclude_assembly_location: list[str] | None = None  # plus-separated on the wire
    exclude_assembly_country: list[str] | None = None
    exclude_exterior_color: list[str] | None = None
    exclude_interior_color: list[str] | None = None
    exclude_base_exterior_color: list[str] | None = None
    exclude_base_interior_color: list[str] | None = None
    exclude_options_packages: list[str] | None = None
    exclude_features: list[str] | None = None
    exclude_fuel_type: list[str] | None = None
    exclude_powertrain_type: list[str] | None = None
    exclude_keywords: list[str] | None = None

    # Range filters (integers, serialized as strings)
    min_price: int | None = None
    max_price: int | None = None
    min_mileage: int | None = None
    max_mileage: int | None = None
    min_msrp: int | None = None
    max_msrp: int | None = None
    min_days_on_market: int | None = None
    max_days_on_market: int | None = None

    # Inventory mode
    inventory_status: InventoryMode = InventoryMode.ACTIVE
    sold_within_days: int | None = None
    snapshot_date: date | None = None

    # Geo
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    radius: float | None = None
    bbox: BBox | None = None

    @model_validator(mode="after")
    def _validate_geo_and_inventory(self) -> "ListingsFilterBase":
        if self.radius is not None:
            has_postal = self.postal_code is not None
            has_latlon = self.latitude is not None and self.longitude is not None
            if not (has_postal ^ has_latlon):
                raise ValueError(
                    "radius requires exactly one of postal_code"
                    " or (latitude + longitude)"
                )
        if self.bbox is not None and self.radius is not None:
            raise ValueError("bbox and radius are mutually exclusive")
        if (
            self.sold_within_days is not None
            and self.inventory_status != InventoryMode.SOLD
        ):
            raise ValueError("sold_within_days requires inventory_status='sold'")
        if (
            self.snapshot_date is not None
            and self.inventory_status != InventoryMode.ACTIVE
        ):
            raise ValueError("snapshot_date requires inventory_status='active'")
        if self.sold_within_days is not None and self.snapshot_date is not None:
            raise ValueError(
                "sold_within_days and snapshot_date are mutually exclusive"
            )
        return self

    def to_params(self) -> dict[str, str]:
        """Serialize to flat query-string params, handling all separator quirks."""
        params: dict[str, str] = {}

        def comma(field: str, values: list[Any]) -> None:
            if values:
                params[field] = ",".join(str(v) for v in values)

        def pipe(field: str, values: list[Any]) -> None:
            if values:
                params[field] = "|".join(str(v) for v in values)

        def plus(field: str, values: list[Any]) -> None:
            if values:
                params[field] = "+".join(str(v) for v in values)

        # Categorical fields (comma-separated)
        for field in [
            "make",
            "model",
            "trim",
            "state",
            "dealer_id",
            "dealer_type",
            "availability_status",
            "inventory_type",
            "body_type",
            "transmission",
            "drivetrain",
            "fuel_type",
            "powertrain_type",
            "engine",
            "version",
            "exterior_color",
            "interior_color",
            "base_exterior_color",
            "base_interior_color",
            "options_packages",
            "features",
            "keywords",
            "vin_pattern",
            "assembly_country",
            "exclude_make",
            "exclude_model",
            "exclude_trim",
            "exclude_state",
            "exclude_inventory_type",
            "exclude_body_type",
            "exclude_transmission",
            "exclude_drivetrain",
            "exclude_version",
            "exclude_engine",
            "exclude_assembly_country",
            "exclude_exterior_color",
            "exclude_interior_color",
            "exclude_base_exterior_color",
            "exclude_base_interior_color",
            "exclude_options_packages",
            "exclude_features",
            "exclude_fuel_type",
            "exclude_powertrain_type",
            "exclude_keywords",
        ]:
            val = getattr(self, field)
            if val is not None:
                comma(field, val)

        # Integer list fields (year, seating_capacity, etc.) — same comma join
        for field in ["year", "seating_capacity", "cylinders", "doors", "exclude_year"]:
            val = getattr(self, field)
            if val is not None:
                comma(field, val)

        # Special separators
        if self.assembly_location:
            pipe("assembly_location", self.assembly_location)
        if self.exclude_assembly_location:
            plus("exclude_assembly_location", self.exclude_assembly_location)

        # Range filters
        for field in [
            "min_price",
            "max_price",
            "min_mileage",
            "max_mileage",
            "min_msrp",
            "max_msrp",
            "min_days_on_market",
            "max_days_on_market",
        ]:
            val = getattr(self, field)
            if val is not None:
                params[field] = str(val)

        # Inventory mode (omit default to keep URLs clean)
        if self.inventory_status != InventoryMode.ACTIVE:
            params["inventory_status"] = self.inventory_status.value
        if self.sold_within_days is not None:
            params["sold_within_days"] = str(self.sold_within_days)
        if self.snapshot_date is not None:
            params["snapshot_date"] = self.snapshot_date.isoformat()

        # Geo
        if self.postal_code is not None:
            params["postal_code"] = self.postal_code
        if self.latitude is not None:
            params["latitude"] = str(self.latitude)
        if self.longitude is not None:
            params["longitude"] = str(self.longitude)
        if self.radius is not None:
            params["radius"] = str(self.radius)
        if self.bbox is not None:
            params["bbox"] = (
                f"{self.bbox.west},{self.bbox.south},{self.bbox.east},{self.bbox.north}"
            )

        return params
