from typing import Literal, TypeAlias

from pydantic import Field, field_validator

from visor.models._base import ListingsFilterBase, VisorResponseModel

FACET_NAMES = {
    "make",
    "model",
    "inventory_type",
    "year",
    "trim",
    "version",
    "base_exterior_color",
    "exterior_color",
    "base_interior_color",
    "interior_color",
    "seating_capacity",
    "doors",
    "engine",
    "state",
    "drivetrain",
    "assembly_location",
    "assembly_country",
    "transmission",
    "fuel_type",
    "body_type",
    "cylinders",
    "dealer_type",
    "availability_status",
    "options_packages",
    "features",
    "keywords",
    "price",
    "msrp",
    "miles",
    "days_on_market",
}

FacetSort: TypeAlias = Literal["count", "-count", "metric", "-metric"]


class FacetsFilter(ListingsFilterBase):
    """Filter for GET /v1/facets. No pagination or projection."""

    facets: list[str]
    facet_value_limit: int | None = None
    metric: str | None = None
    sort: FacetSort = "-count"

    @field_validator("facets")
    @classmethod
    def _validate_facets(cls, v: list[str]) -> list[str]:
        unknown = set(v) - FACET_NAMES
        if unknown:
            raise ValueError(f"unknown facets: {unknown}")
        return v

    def to_params(self) -> dict[str, str]:
        params = super().to_params()
        params["facets"] = ",".join(self.facets)
        if self.facet_value_limit is not None:
            params["facet_value_limit"] = str(self.facet_value_limit)
        if self.metric is not None:
            params["metric"] = self.metric
        params["sort"] = self.sort
        return params


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class FacetBucket(VisorResponseModel):
    value: str
    count: int | None = None
    metric: float | None = None


class RangeBucket(VisorResponseModel):
    min: float
    max: float
    count: int


class RangeFacet(VisorResponseModel):
    buckets: list[RangeBucket]
    interval: float
    min: float
    max: float


class FieldStats(VisorResponseModel):
    min: float
    max: float
    count: int
    missing: int
    mean: float
    median: float
    stddev: float


class FacetsData(VisorResponseModel):
    total: int
    facets: dict[str, list[FacetBucket]] = Field(default_factory=dict)
    range_facets: dict[str, RangeFacet] = Field(default_factory=dict)
    stats: dict[str, FieldStats] = Field(default_factory=dict)


class FacetsMeta(VisorResponseModel):
    facets: list[str]
    metric: str
    sort: str
    minimum_metric_count: int


class FacetsResponse(VisorResponseModel):
    data: FacetsData
    meta: FacetsMeta
