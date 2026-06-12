import os
from datetime import date
from typing import Literal

from visor._transport import DEFAULT_BASE_URL, AsyncVisorTransport
from visor.models.dealers import DealerDetail, DealerFilter, DealersPage
from visor.models.facets import FacetsFilter, FacetsResponse
from visor.models.listings import ListingDetail, ListingsFilter, ListingsPage
from visor.models.usage import UsageSummary
from visor.models.vins import VinDetail


class AsyncVisorClient:
    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 30.0,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        key = api_key or os.environ.get("VISOR_API_KEY")
        if not key:
            raise ValueError(
                "api_key is required. Pass it directly or set VISOR_API_KEY."
            )
        self._transport = AsyncVisorTransport(key, base_url=base_url, timeout=timeout)

    async def __aenter__(self) -> "AsyncVisorClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._transport.aclose()

    # ------------------------------------------------------------------ #
    # Inventory                                                            #
    # ------------------------------------------------------------------ #

    async def filter_listings(
        self, filter: ListingsFilter | None = None
    ) -> ListingsPage:
        params = (filter or ListingsFilter()).to_params()
        data = await self._transport.get("/listings", params)
        return ListingsPage.model_validate(data)

    async def get_listing(
        self,
        listing_id: str,
        include: list[Literal["price_history", "options"]] | None = None,
    ) -> ListingDetail:
        params: dict[str, str] = {}
        if include:
            params["include"] = ",".join(include)
        data = await self._transport.get(f"/listings/{listing_id}", params)
        return ListingDetail.model_validate(data["data"])

    async def lookup_vin(
        self,
        vin: str,
        include: list[Literal["price_history", "options"]] | None = None,
    ) -> VinDetail:
        params: dict[str, str] = {}
        if include:
            params["include"] = ",".join(include)
        data = await self._transport.get(f"/vins/{vin}", params)
        return VinDetail.model_validate(data["data"])

    async def filter_facets(self, filter: FacetsFilter) -> FacetsResponse:
        data = await self._transport.get("/facets", filter.to_params())
        return FacetsResponse.model_validate(data)

    # ------------------------------------------------------------------ #
    # Dealers                                                              #
    # ------------------------------------------------------------------ #

    async def search_dealers(self, filter: DealerFilter | None = None) -> DealersPage:
        params = (filter or DealerFilter()).to_params()
        data = await self._transport.get("/dealers", params)
        return DealersPage.model_validate(data)

    async def get_dealer(self, dealer_id: str) -> DealerDetail:
        data = await self._transport.get(f"/dealers/{dealer_id}")
        return DealerDetail.model_validate(data["data"])

    async def dealer_inventory(
        self,
        dealer_id: str,
        filter: ListingsFilter | None = None,
    ) -> ListingsPage:
        params = (filter or ListingsFilter()).to_params()
        data = await self._transport.get(f"/dealers/{dealer_id}/listings", params)
        return ListingsPage.model_validate(data)

    # ------------------------------------------------------------------ #
    # Usage                                                                #
    # ------------------------------------------------------------------ #

    async def get_usage(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        metering_class: list[str] | None = None,
    ) -> UsageSummary:
        params: dict[str, str] = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        if metering_class:
            params["metering_class"] = ",".join(metering_class)
        data = await self._transport.get("/usage", params)
        return UsageSummary.model_validate(data)
