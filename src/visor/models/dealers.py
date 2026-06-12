from typing import Literal

from pydantic import Field

from visor.models._base import Pagination, VisorRequestModel, VisorResponseModel


class DealerFilter(VisorRequestModel):
    limit: int = 50
    offset: int = 0
    dealer_id: list[str] | None = None
    state: list[str] | None = None
    country: str | None = None
    type: Literal["franchise", "independent"] | None = None
    make: list[str] | None = None
    q: str | None = None

    def to_params(self) -> dict[str, str]:
        params: dict[str, str] = {
            "limit": str(self.limit),
            "offset": str(self.offset),
        }
        if self.dealer_id:
            params["dealer_id"] = ",".join(self.dealer_id)
        if self.state:
            params["state"] = ",".join(self.state)
        if self.country:
            params["country"] = self.country
        if self.type:
            params["type"] = self.type
        if self.make:
            params["make"] = ",".join(self.make)
        if self.q:
            params["q"] = self.q
        return params


class DealerAddress(VisorResponseModel):
    line1: str | None = None
    city: str
    state: str
    country: str


class DealerSummary(VisorResponseModel):
    dealer_id: str
    name: str
    city: str
    state: str
    country: str
    latitude: float | None = None
    longitude: float | None = None
    type: str
    website: str | None = None
    makes: list[str] = Field(default_factory=list)
    listing_count: int


class DealerDetail(DealerSummary):
    phone: str | None = None
    address: DealerAddress | None = None


class DealersPage(VisorResponseModel):
    data: list[DealerSummary]
    pagination: Pagination
    meta: dict[str, object] = Field(default_factory=dict)
