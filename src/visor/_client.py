import os
from datetime import date
from typing import Literal

from visor._transport import DEFAULT_BASE_URL, AsyncVisorTransport, SyncVisorTransport
from visor.models.dealers import DealerDetail, DealerFilter, DealersPage
from visor.models.facets import FacetsFilter, FacetsResponse
from visor.models.listings import ListingDetail, ListingsFilter, ListingsPage
from visor.models.usage import UsageSummary
from visor.models.vins import VinDetail


class AsyncVisorClient:
    """Async client for the Visor Public API.

    All methods are coroutines and must be awaited. Use as an async context
    manager to ensure the underlying HTTP connection pool is closed:

        async with AsyncVisorClient() as client:
            page = await client.filter_listings(...)

    Args:
        api_key: Visor API key. Defaults to the ``VISOR_API_KEY`` environment
            variable.
        timeout: Request timeout in seconds. Defaults to 30.
        base_url: API base URL. Override for local testing or staging.

    Raises:
        ValueError: If no API key is provided or found in the environment.
    """

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
        """Close the underlying HTTP client and release connections."""
        await self._transport.aclose()

    # ------------------------------------------------------------------ #
    # Inventory                                                            #
    # ------------------------------------------------------------------ #

    async def filter_listings(
        self, filter: ListingsFilter | None = None
    ) -> ListingsPage:
        """Return a single page of listings matching the given filter.

        To iterate all results across pages, use :func:`visor.paginate_listings`
        instead.

        Args:
            filter: Search and pagination criteria. Defaults to an empty filter
                (first page, no constraints).

        Returns:
            A :class:`~visor.models.listings.ListingsPage` containing the
            matched listings and pagination metadata.

        Raises:
            AuthError: Invalid or missing API key (HTTP 401).
            ForbiddenError: Key lacks access to this resource (HTTP 403).
            RateLimitError: Rate limit exceeded; check ``.retry_after``.
            VisorAPIError: Any other API-level error.
            VisorTransportError: Network-level failure (timeout, connection).
        """
        params = (filter or ListingsFilter()).to_params()
        data = await self._transport.get("/listings", params)
        return ListingsPage.model_validate(data)

    async def get_listing(
        self,
        listing_id: str,
        include: list[Literal["price_history", "options"]] | None = None,
    ) -> ListingDetail:
        """Return full detail for a single listing by its ID.

        Args:
            listing_id: The unique listing identifier.
            include: Optional extra sections to embed in the response.
                ``"price_history"`` adds historical price records;
                ``"options"`` adds option/package details.

        Returns:
            A :class:`~visor.models.listings.ListingDetail` for the requested
            listing.

        Raises:
            NotFoundError: No listing with that ID exists (HTTP 404).
            AuthError: Invalid or missing API key (HTTP 401).
            ForbiddenError: Key lacks access to this resource (HTTP 403).
            RateLimitError: Rate limit exceeded; check ``.retry_after``.
            VisorAPIError: Any other API-level error.
            VisorTransportError: Network-level failure.
        """
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
        """Return build and listing information for a VIN.

        The returned :class:`~visor.models.vins.VinDetail` always includes
        ``vin``, ``status``, and ``build``. The ``latest_listing`` field is
        ``None`` when no active or recent listing exists for the VIN.

        Args:
            vin: 17-character Vehicle Identification Number.
            include: Optional extra sections to embed. ``"price_history"``
                adds historical price records; ``"options"`` adds option
                details on the latest listing.

        Returns:
            A :class:`~visor.models.vins.VinDetail` for the requested VIN.

        Raises:
            NotFoundError: VIN not found in the Visor database (HTTP 404).
            AuthError: Invalid or missing API key (HTTP 401).
            ForbiddenError: Key lacks access to this resource (HTTP 403).
            RateLimitError: Rate limit exceeded; check ``.retry_after``.
            VisorAPIError: Any other API-level error.
            VisorTransportError: Network-level failure.
        """
        params: dict[str, str] = {}
        if include:
            params["include"] = ",".join(include)
        data = await self._transport.get(f"/vins/{vin}", params)
        return VinDetail.model_validate(data["data"])

    async def filter_facets(self, filter: FacetsFilter) -> FacetsResponse:
        """Return facet aggregations for the given filter.

        Facets summarize available field values and ranges across all listings
        matching the filter, useful for building search-UI refinement panels.

        Args:
            filter: Facet query criteria, including which facets to compute.

        Returns:
            A :class:`~visor.models.facets.FacetsResponse` with aggregation
            data for each requested facet.

        Raises:
            AuthError: Invalid or missing API key (HTTP 401).
            ForbiddenError: Key lacks access to this resource (HTTP 403).
            RateLimitError: Rate limit exceeded; check ``.retry_after``.
            VisorAPIError: Any other API-level error.
            VisorTransportError: Network-level failure.
        """
        data = await self._transport.get("/facets", filter.to_params())
        return FacetsResponse.model_validate(data)

    # ------------------------------------------------------------------ #
    # Dealers                                                              #
    # ------------------------------------------------------------------ #

    async def search_dealers(self, filter: DealerFilter | None = None) -> DealersPage:
        """Return a single page of dealers matching the given filter.

        To iterate all dealers across pages, use :func:`visor.paginate_dealers`
        instead.

        Args:
            filter: Search criteria and pagination parameters. Defaults to an
                empty filter (first page, no constraints).

        Returns:
            A :class:`~visor.models.dealers.DealersPage` containing matched
            dealers and pagination metadata.

        Raises:
            AuthError: Invalid or missing API key (HTTP 401).
            ForbiddenError: Key lacks access to this resource (HTTP 403).
            RateLimitError: Rate limit exceeded; check ``.retry_after``.
            VisorAPIError: Any other API-level error.
            VisorTransportError: Network-level failure.
        """
        params = (filter or DealerFilter()).to_params()
        data = await self._transport.get("/dealers", params)
        return DealersPage.model_validate(data)

    async def get_dealer(self, dealer_id: str) -> DealerDetail:
        """Return full detail for a single dealer by its ID.

        Args:
            dealer_id: The unique dealer identifier.

        Returns:
            A :class:`~visor.models.dealers.DealerDetail` for the requested
            dealer.

        Raises:
            NotFoundError: No dealer with that ID exists (HTTP 404).
            AuthError: Invalid or missing API key (HTTP 401).
            ForbiddenError: Key lacks access to this resource (HTTP 403).
            RateLimitError: Rate limit exceeded; check ``.retry_after``.
            VisorAPIError: Any other API-level error.
            VisorTransportError: Network-level failure.
        """
        data = await self._transport.get(f"/dealers/{dealer_id}")
        return DealerDetail.model_validate(data["data"])

    async def dealer_inventory(
        self,
        dealer_id: str,
        filter: ListingsFilter | None = None,
    ) -> ListingsPage:
        """Return a single page of inventory for a specific dealer.

        Accepts the same :class:`~visor.models.listings.ListingsFilter` shape
        as :meth:`filter_listings`, so you can reuse a filter object across
        both methods. Call this method in a loop advancing ``filter.offset`` to
        paginate through all inventory pages.

        Args:
            dealer_id: The unique dealer identifier.
            filter: Optional search and pagination criteria.

        Returns:
            A :class:`~visor.models.listings.ListingsPage` of the dealer's
            inventory.

        Raises:
            NotFoundError: No dealer with that ID exists (HTTP 404).
            AuthError: Invalid or missing API key (HTTP 401).
            ForbiddenError: Key lacks access to this resource (HTTP 403).
            RateLimitError: Rate limit exceeded; check ``.retry_after``.
            VisorAPIError: Any other API-level error.
            VisorTransportError: Network-level failure.
        """
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
        """Return API usage statistics for your account.

        All parameters are optional. Omitting date bounds returns the full
        available history. Omitting ``metering_class`` returns all endpoint
        categories.

        Args:
            start_date: Start of the reporting window (inclusive).
            end_date: End of the reporting window (inclusive).
            metering_class: Endpoint categories to include, e.g.
                ``["listings", "dealers"]``. Returns all categories when
                omitted.

        Returns:
            A :class:`~visor.models.usage.UsageSummary` with request counts
            and quota details.

        Raises:
            AuthError: Invalid or missing API key (HTTP 401).
            ForbiddenError: Key lacks access to this resource (HTTP 403).
            RateLimitError: Rate limit exceeded; check ``.retry_after``.
            VisorAPIError: Any other API-level error.
            VisorTransportError: Network-level failure.
        """
        params: dict[str, str] = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        if metering_class:
            params["metering_class"] = ",".join(metering_class)
        data = await self._transport.get("/usage", params)
        return UsageSummary.model_validate(data)


class VisorClient:
    """Synchronous client for the Visor Public API.

    All methods block until the HTTP response is received. The client owns an
    internal :class:`httpx.Client` with a connection pool; it is **not**
    thread-safe. If you share a single ``VisorClient`` across threads, you must
    add external synchronization — or create one client per thread instead.

    Use as a context manager to ensure the connection pool is released:

        with VisorClient() as client:
            page = client.filter_listings(...)

    Args:
        api_key: Visor API key. Defaults to the ``VISOR_API_KEY`` environment
            variable.
        timeout: Request timeout in seconds. Defaults to 30.
        base_url: API base URL. Override for local testing or staging.

    Raises:
        ValueError: If no API key is provided or found in the environment.
    """

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
        self._transport = SyncVisorTransport(key, base_url=base_url, timeout=timeout)

    def __enter__(self) -> "VisorClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client and release connections."""
        self._transport.close()

    # ------------------------------------------------------------------ #
    # Inventory                                                            #
    # ------------------------------------------------------------------ #

    def filter_listings(self, filter: ListingsFilter | None = None) -> ListingsPage:
        """Return a single page of listings matching the given filter.

        To iterate all results across pages, use :func:`visor.iter_listings`
        instead.

        Args:
            filter: Search and pagination criteria. Defaults to an empty filter
                (first page, no constraints).

        Returns:
            A :class:`~visor.models.listings.ListingsPage` containing the
            matched listings and pagination metadata.

        Raises:
            AuthError: Invalid or missing API key (HTTP 401).
            ForbiddenError: Key lacks access to this resource (HTTP 403).
            RateLimitError: Rate limit exceeded; check ``.retry_after``.
            VisorAPIError: Any other API-level error.
            VisorTransportError: Network-level failure (timeout, connection).
        """
        params = (filter or ListingsFilter()).to_params()
        data = self._transport.get("/listings", params)
        return ListingsPage.model_validate(data)

    def get_listing(
        self,
        listing_id: str,
        include: list[Literal["price_history", "options"]] | None = None,
    ) -> ListingDetail:
        """Return full detail for a single listing by its ID.

        Args:
            listing_id: The unique listing identifier.
            include: Optional extra sections to embed in the response.
                ``"price_history"`` adds historical price records;
                ``"options"`` adds option/package details.

        Returns:
            A :class:`~visor.models.listings.ListingDetail` for the requested
            listing.

        Raises:
            NotFoundError: No listing with that ID exists (HTTP 404).
            AuthError: Invalid or missing API key (HTTP 401).
            ForbiddenError: Key lacks access to this resource (HTTP 403).
            RateLimitError: Rate limit exceeded; check ``.retry_after``.
            VisorAPIError: Any other API-level error.
            VisorTransportError: Network-level failure.
        """
        params: dict[str, str] = {}
        if include:
            params["include"] = ",".join(include)
        data = self._transport.get(f"/listings/{listing_id}", params)
        return ListingDetail.model_validate(data["data"])

    def lookup_vin(
        self,
        vin: str,
        include: list[Literal["price_history", "options"]] | None = None,
    ) -> VinDetail:
        """Return build and listing information for a VIN.

        The returned :class:`~visor.models.vins.VinDetail` always includes
        ``vin``, ``status``, and ``build``. The ``latest_listing`` field is
        ``None`` when no active or recent listing exists for the VIN.

        Args:
            vin: 17-character Vehicle Identification Number.
            include: Optional extra sections to embed. ``"price_history"``
                adds historical price records; ``"options"`` adds option
                details on the latest listing.

        Returns:
            A :class:`~visor.models.vins.VinDetail` for the requested VIN.

        Raises:
            NotFoundError: VIN not found in the Visor database (HTTP 404).
            AuthError: Invalid or missing API key (HTTP 401).
            ForbiddenError: Key lacks access to this resource (HTTP 403).
            RateLimitError: Rate limit exceeded; check ``.retry_after``.
            VisorAPIError: Any other API-level error.
            VisorTransportError: Network-level failure.
        """
        params: dict[str, str] = {}
        if include:
            params["include"] = ",".join(include)
        data = self._transport.get(f"/vins/{vin}", params)
        return VinDetail.model_validate(data["data"])

    def filter_facets(self, filter: FacetsFilter) -> FacetsResponse:
        """Return facet aggregations for the given filter.

        Facets summarize available field values and ranges across all listings
        matching the filter, useful for building search-UI refinement panels.

        Args:
            filter: Facet query criteria, including which facets to compute.

        Returns:
            A :class:`~visor.models.facets.FacetsResponse` with aggregation
            data for each requested facet.

        Raises:
            AuthError: Invalid or missing API key (HTTP 401).
            ForbiddenError: Key lacks access to this resource (HTTP 403).
            RateLimitError: Rate limit exceeded; check ``.retry_after``.
            VisorAPIError: Any other API-level error.
            VisorTransportError: Network-level failure.
        """
        data = self._transport.get("/facets", filter.to_params())
        return FacetsResponse.model_validate(data)

    # ------------------------------------------------------------------ #
    # Dealers                                                              #
    # ------------------------------------------------------------------ #

    def search_dealers(self, filter: DealerFilter | None = None) -> DealersPage:
        """Return a single page of dealers matching the given filter.

        To iterate all dealers across pages, use :func:`visor.iter_dealers`
        instead.

        Args:
            filter: Search criteria and pagination parameters. Defaults to an
                empty filter (first page, no constraints).

        Returns:
            A :class:`~visor.models.dealers.DealersPage` containing matched
            dealers and pagination metadata.

        Raises:
            AuthError: Invalid or missing API key (HTTP 401).
            ForbiddenError: Key lacks access to this resource (HTTP 403).
            RateLimitError: Rate limit exceeded; check ``.retry_after``.
            VisorAPIError: Any other API-level error.
            VisorTransportError: Network-level failure.
        """
        params = (filter or DealerFilter()).to_params()
        data = self._transport.get("/dealers", params)
        return DealersPage.model_validate(data)

    def get_dealer(self, dealer_id: str) -> DealerDetail:
        """Return full detail for a single dealer by its ID.

        Args:
            dealer_id: The unique dealer identifier.

        Returns:
            A :class:`~visor.models.dealers.DealerDetail` for the requested
            dealer.

        Raises:
            NotFoundError: No dealer with that ID exists (HTTP 404).
            AuthError: Invalid or missing API key (HTTP 401).
            ForbiddenError: Key lacks access to this resource (HTTP 403).
            RateLimitError: Rate limit exceeded; check ``.retry_after``.
            VisorAPIError: Any other API-level error.
            VisorTransportError: Network-level failure.
        """
        data = self._transport.get(f"/dealers/{dealer_id}")
        return DealerDetail.model_validate(data["data"])

    def dealer_inventory(
        self,
        dealer_id: str,
        filter: ListingsFilter | None = None,
    ) -> ListingsPage:
        """Return a single page of inventory for a specific dealer.

        Accepts the same :class:`~visor.models.listings.ListingsFilter` shape
        as :meth:`filter_listings`, so you can reuse a filter object across
        both methods. Call this method in a loop advancing ``filter.offset`` to
        paginate through all inventory pages.

        Args:
            dealer_id: The unique dealer identifier.
            filter: Optional search and pagination criteria.

        Returns:
            A :class:`~visor.models.listings.ListingsPage` of the dealer's
            inventory.

        Raises:
            NotFoundError: No dealer with that ID exists (HTTP 404).
            AuthError: Invalid or missing API key (HTTP 401).
            ForbiddenError: Key lacks access to this resource (HTTP 403).
            RateLimitError: Rate limit exceeded; check ``.retry_after``.
            VisorAPIError: Any other API-level error.
            VisorTransportError: Network-level failure.
        """
        params = (filter or ListingsFilter()).to_params()
        data = self._transport.get(f"/dealers/{dealer_id}/listings", params)
        return ListingsPage.model_validate(data)

    # ------------------------------------------------------------------ #
    # Usage                                                                #
    # ------------------------------------------------------------------ #

    def get_usage(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        metering_class: list[str] | None = None,
    ) -> UsageSummary:
        """Return API usage statistics for your account.

        All parameters are optional. Omitting date bounds returns the full
        available history. Omitting ``metering_class`` returns all endpoint
        categories.

        Args:
            start_date: Start of the reporting window (inclusive).
            end_date: End of the reporting window (inclusive).
            metering_class: Endpoint categories to include, e.g.
                ``["listings", "dealers"]``. Returns all categories when
                omitted.

        Returns:
            A :class:`~visor.models.usage.UsageSummary` with request counts
            and quota details.

        Raises:
            AuthError: Invalid or missing API key (HTTP 401).
            ForbiddenError: Key lacks access to this resource (HTTP 403).
            RateLimitError: Rate limit exceeded; check ``.retry_after``.
            VisorAPIError: Any other API-level error.
            VisorTransportError: Network-level failure.
        """
        params: dict[str, str] = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        if metering_class:
            params["metering_class"] = ",".join(metering_class)
        data = self._transport.get("/usage", params)
        return UsageSummary.model_validate(data)
