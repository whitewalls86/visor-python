from datetime import date
from typing import Literal

from pydantic import Field, field_validator

from visor.models._base import (
    DealerRef,
    ListingsFilterBase,
    Pagination,
    PriceHistoryEntry,
    SortOrder,
    VehicleOption,
    VehicleRecord,
    VisorResponseModel,
)

LISTING_FIELDS = {
    "default",
    "id",
    "vin",
    "year",
    "make",
    "model",
    "trim",
    "version",
    "body_type",
    "drivetrain",
    "fuel_type",
    "powertrain_type",
    "transmission",
    "engine",
    "cylinders",
    "doors",
    "seating_capacity",
    "exterior_color",
    "interior_color",
    "base_exterior_color",
    "base_interior_color",
    "msrp",
    "discount_from_msrp",
    "price",
    "miles",
    "days_on_market",
    "status",
    "inventory_status",
    "inventory_type",
    "stock_number",
    "vdp_url",
    "sold_date",
    "dealer_id",
    "dealer_name",
    "dealer_type",
    "city",
    "state",
    "latitude",
    "longitude",
    "distance_miles",
    "photo_urls",
    "features",
    "options_packages",
}


class ListingsFilter(ListingsFilterBase):
    limit: int = 50
    offset: int = 0
    sort: SortOrder = SortOrder.DAYS_ON_MARKET
    fields: list[str] | None = None
    include: list[Literal["price_history", "options"]] | None = None

    @field_validator("limit")
    @classmethod
    def _limit_max(cls, v: int) -> int:
        if v > 100:
            raise ValueError("limit maximum is 100")
        return v

    @field_validator("fields")
    @classmethod
    def _validate_fields(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            unknown = set(v) - LISTING_FIELDS
            if unknown:
                raise ValueError(f"unknown fields: {unknown}")
        return v

    def to_params(self) -> dict[str, str]:
        params = super().to_params()
        params["limit"] = str(self.limit)
        params["offset"] = str(self.offset)
        params["sort"] = self.sort.value
        if self.fields:
            params["fields"] = ",".join(self.fields)
        if self.include:
            params["include"] = ",".join(self.include)
        return params


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class ListingSummary(VisorResponseModel):
    """Returned by filter_listings() and dealer_inventory().

    id and vin are always present; the API returns them regardless of fields
    projection. All other fields are optional because the caller controls which
    fields are returned via ListingsFilter.fields.
    """

    id: str
    vin: str
    year: int | None = None
    make: str | None = None
    model: str | None = None
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
    msrp: int | None = None
    discount_from_msrp: int | None = None
    price: int | None = None
    miles: int | None = None
    days_on_market: int | None = None
    status: str | None = None
    inventory_status: str | None = None
    inventory_type: str | None = None
    stock_number: str | None = None
    vdp_url: str | None = None
    sold_date: date | None = None
    dealer_id: str | None = None
    dealer_name: str | None = None
    dealer_type: str | None = None
    city: str | None = None
    state: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    distance_miles: float | None = None
    photo_urls: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    options_packages: list[str] = Field(default_factory=list)
    price_history: list[PriceHistoryEntry] = Field(default_factory=list)
    options: list[VehicleOption] = Field(default_factory=list)


class ListingDetail(VisorResponseModel):
    """Returned by get_listing() — always fully populated."""

    id: str
    vin: str
    status: str
    price: int | None = None
    miles: int | None = None
    inventory_type: str
    stock_number: str | None = None
    vdp_url: str | None = None
    vhr_url: str | None = None
    photo_urls: list[str] = Field(default_factory=list)
    photo_url_primary: str | None = None
    inventory_date: date | None = None
    sold_date: date | None = None
    last_checked_at: str | None = None
    dealer: DealerRef
    vehicle: VehicleRecord
    price_history: list[PriceHistoryEntry] = Field(default_factory=list)


class ListingSnapshot(VisorResponseModel):
    """Embedded listing inside VinDetail.latest_listing.

    Differs from ListingDetail: no top-level vin/status/vehicle fields.
    """

    id: str
    price: int | None = None
    miles: int | None = None
    inventory_type: str
    stock_number: str | None = None
    vdp_url: str | None = None
    vhr_url: str | None = None
    photo_urls: list[str] = Field(default_factory=list)
    photo_url_primary: str | None = None
    inventory_date: date | None = None
    sold_date: date | None = None
    last_checked_at: str | None = None
    dealer: DealerRef
    price_history: list[PriceHistoryEntry] = Field(default_factory=list)


class ListingsPage(VisorResponseModel):
    data: list[ListingSummary]
    pagination: Pagination
    meta: dict[str, object] = Field(default_factory=dict)
