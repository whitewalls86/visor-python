"""Tests for pagination helpers in _pagination.py."""

from __future__ import annotations

import pytest

from visor._pagination import (
    iter_dealers,
    iter_listings,
    paginate_dealers,
    paginate_listings,
)
from visor.models._base import Pagination
from visor.models.dealers import DealerFilter, DealersPage, DealerSummary
from visor.models.listings import ListingsFilter, ListingsPage, ListingSummary

# ---------------------------------------------------------------------------
# Helpers to build minimal model instances
# ---------------------------------------------------------------------------


def _listing(id: str) -> ListingSummary:
    return ListingSummary(id=id, vin="1HGCM82633A000000")


def _dealer(dealer_id: str) -> DealerSummary:
    return DealerSummary(
        dealer_id=dealer_id,
        name="Test Dealer",
        city="Austin",
        state="TX",
        country="US",
        type="franchise",
        listing_count=10,
    )


def _listings_page(
    items: list[ListingSummary],
    next_offset: int | None,
    offset: int = 0,
) -> ListingsPage:
    return ListingsPage(
        data=items,
        pagination=Pagination(limit=2, offset=offset, total=4, next_offset=next_offset),
        meta={},
    )


def _dealers_page(
    items: list[DealerSummary],
    next_offset: int | None,
    offset: int = 0,
) -> DealersPage:
    return DealersPage(
        data=items,
        pagination=Pagination(limit=2, offset=offset, total=4, next_offset=next_offset),
        meta={},
    )


# ---------------------------------------------------------------------------
# Fake async client
# ---------------------------------------------------------------------------


class FakeAsyncClient:
    def __init__(
        self,
        listing_pages: list[ListingsPage],
        dealer_pages: list[DealersPage],
    ) -> None:
        self._listing_pages = iter(listing_pages)
        self._dealer_pages = iter(dealer_pages)
        self.listing_calls: list[ListingsFilter] = []
        self.dealer_calls: list[DealerFilter] = []

    async def filter_listings(
        self, filter: ListingsFilter | None = None
    ) -> ListingsPage:
        self.listing_calls.append(filter or ListingsFilter())
        return next(self._listing_pages)

    async def search_dealers(self, filter: DealerFilter | None = None) -> DealersPage:
        self.dealer_calls.append(filter or DealerFilter())
        return next(self._dealer_pages)


# ---------------------------------------------------------------------------
# Fake sync client
# ---------------------------------------------------------------------------


class FakeSyncClient:
    def __init__(
        self,
        listing_pages: list[ListingsPage],
        dealer_pages: list[DealersPage],
    ) -> None:
        self._listing_pages = iter(listing_pages)
        self._dealer_pages = iter(dealer_pages)
        self.listing_calls: list[ListingsFilter] = []
        self.dealer_calls: list[DealerFilter] = []

    def filter_listings(self, filter: ListingsFilter | None = None) -> ListingsPage:
        self.listing_calls.append(filter or ListingsFilter())
        return next(self._listing_pages)

    def search_dealers(self, filter: DealerFilter | None = None) -> DealersPage:
        self.dealer_calls.append(filter or DealerFilter())
        return next(self._dealer_pages)


# ---------------------------------------------------------------------------
# paginate_listings
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_paginate_listings_two_pages() -> None:
    page1 = _listings_page([_listing("a"), _listing("b")], next_offset=2)
    page2 = _listings_page([_listing("c"), _listing("d")], next_offset=None, offset=2)
    client = FakeAsyncClient([page1, page2], [])

    results = [item async for item in paginate_listings(client)]

    assert [r.id for r in results] == ["a", "b", "c", "d"]
    assert len(client.listing_calls) == 2
    assert client.listing_calls[0].offset == 0
    assert client.listing_calls[1].offset == 2


@pytest.mark.asyncio
async def test_paginate_listings_stops_on_none_next_offset() -> None:
    page = _listings_page([_listing("x")], next_offset=None)
    client = FakeAsyncClient([page], [])

    results = [item async for item in paginate_listings(client)]

    assert len(results) == 1
    assert len(client.listing_calls) == 1


@pytest.mark.asyncio
async def test_paginate_listings_max_pages() -> None:
    page1 = _listings_page([_listing("a")], next_offset=1)
    page2 = _listings_page([_listing("b")], next_offset=2)
    client = FakeAsyncClient([page1, page2], [])

    results = [item async for item in paginate_listings(client, max_pages=1)]

    assert [r.id for r in results] == ["a"]
    assert len(client.listing_calls) == 1


@pytest.mark.asyncio
async def test_paginate_listings_max_pages_zero_yields_nothing() -> None:
    client = FakeAsyncClient([], [])
    results = [item async for item in paginate_listings(client, max_pages=0)]
    assert results == []
    assert client.listing_calls == []


@pytest.mark.asyncio
async def test_paginate_listings_does_not_mutate_original_filter() -> None:
    page1 = _listings_page([_listing("a")], next_offset=2)
    page2 = _listings_page([_listing("b")], next_offset=None, offset=2)
    client = FakeAsyncClient([page1, page2], [])

    original = ListingsFilter(offset=0, make=["Toyota"])
    _ = [item async for item in paginate_listings(client, original)]

    assert original.offset == 0


@pytest.mark.asyncio
async def test_paginate_listings_none_filter_uses_defaults() -> None:
    page = _listings_page([_listing("a")], next_offset=None)
    client = FakeAsyncClient([page], [])

    _ = [item async for item in paginate_listings(client, None)]

    assert len(client.listing_calls) == 1
    assert client.listing_calls[0] == ListingsFilter()


# ---------------------------------------------------------------------------
# paginate_dealers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_paginate_dealers_two_pages() -> None:
    page1 = _dealers_page([_dealer("d1"), _dealer("d2")], next_offset=2)
    page2 = _dealers_page([_dealer("d3"), _dealer("d4")], next_offset=None, offset=2)
    client = FakeAsyncClient([], [page1, page2])

    results = [item async for item in paginate_dealers(client)]

    assert [r.dealer_id for r in results] == ["d1", "d2", "d3", "d4"]
    assert len(client.dealer_calls) == 2
    assert client.dealer_calls[1].offset == 2


@pytest.mark.asyncio
async def test_paginate_dealers_max_pages() -> None:
    page1 = _dealers_page([_dealer("d1")], next_offset=1)
    page2 = _dealers_page([_dealer("d2")], next_offset=2)
    client = FakeAsyncClient([], [page1, page2])

    results = [item async for item in paginate_dealers(client, max_pages=1)]

    assert [r.dealer_id for r in results] == ["d1"]


@pytest.mark.asyncio
async def test_paginate_dealers_stops_on_none_next_offset() -> None:
    page = _dealers_page([_dealer("d1")], next_offset=None)
    client = FakeAsyncClient([], [page])

    results = [item async for item in paginate_dealers(client)]

    assert len(results) == 1
    assert len(client.dealer_calls) == 1


@pytest.mark.asyncio
async def test_paginate_dealers_max_pages_zero_yields_nothing() -> None:
    client = FakeAsyncClient([], [])
    results = [item async for item in paginate_dealers(client, max_pages=0)]
    assert results == []
    assert client.dealer_calls == []


@pytest.mark.asyncio
async def test_paginate_dealers_none_filter_uses_defaults() -> None:
    page = _dealers_page([_dealer("d1")], next_offset=None)
    client = FakeAsyncClient([], [page])

    _ = [item async for item in paginate_dealers(client, None)]

    assert len(client.dealer_calls) == 1
    assert client.dealer_calls[0] == DealerFilter()


@pytest.mark.asyncio
async def test_paginate_dealers_does_not_mutate_original_filter() -> None:
    page1 = _dealers_page([_dealer("d1")], next_offset=2)
    page2 = _dealers_page([_dealer("d2")], next_offset=None, offset=2)
    client = FakeAsyncClient([], [page1, page2])

    original = DealerFilter(offset=0, state=["TX"])
    _ = [item async for item in paginate_dealers(client, original)]

    assert original.offset == 0


# ---------------------------------------------------------------------------
# iter_listings (sync)
# ---------------------------------------------------------------------------


def test_iter_listings_two_pages() -> None:
    page1 = _listings_page([_listing("a"), _listing("b")], next_offset=2)
    page2 = _listings_page([_listing("c"), _listing("d")], next_offset=None, offset=2)
    client = FakeSyncClient([page1, page2], [])

    results = list(iter_listings(client))

    assert [r.id for r in results] == ["a", "b", "c", "d"]
    assert len(client.listing_calls) == 2
    assert client.listing_calls[1].offset == 2


def test_iter_listings_max_pages() -> None:
    page1 = _listings_page([_listing("a")], next_offset=1)
    page2 = _listings_page([_listing("b")], next_offset=2)
    client = FakeSyncClient([page1, page2], [])

    results = list(iter_listings(client, max_pages=1))

    assert [r.id for r in results] == ["a"]
    assert len(client.listing_calls) == 1


def test_iter_listings_max_pages_zero_yields_nothing() -> None:
    client = FakeSyncClient([], [])
    results = list(iter_listings(client, max_pages=0))
    assert results == []


def test_iter_listings_does_not_mutate_original_filter() -> None:
    page1 = _listings_page([_listing("a")], next_offset=2)
    page2 = _listings_page([_listing("b")], next_offset=None, offset=2)
    client = FakeSyncClient([page1, page2], [])

    original = ListingsFilter(offset=0, make=["Honda"])
    list(iter_listings(client, original))

    assert original.offset == 0


def test_iter_listings_none_filter_uses_defaults() -> None:
    page = _listings_page([_listing("a")], next_offset=None)
    client = FakeSyncClient([page], [])

    list(iter_listings(client, None))

    assert client.listing_calls[0] == ListingsFilter()


# ---------------------------------------------------------------------------
# iter_dealers (sync)
# ---------------------------------------------------------------------------


def test_iter_dealers_two_pages() -> None:
    page1 = _dealers_page([_dealer("d1"), _dealer("d2")], next_offset=2)
    page2 = _dealers_page([_dealer("d3"), _dealer("d4")], next_offset=None, offset=2)
    client = FakeSyncClient([], [page1, page2])

    results = list(iter_dealers(client))

    assert [r.dealer_id for r in results] == ["d1", "d2", "d3", "d4"]
    assert len(client.dealer_calls) == 2
    assert client.dealer_calls[0].offset == 0
    assert client.dealer_calls[1].offset == 2


def test_iter_dealers_max_pages() -> None:
    page1 = _dealers_page([_dealer("d1")], next_offset=1)
    page2 = _dealers_page([_dealer("d2")], next_offset=2)
    client = FakeSyncClient([], [page1, page2])

    results = list(iter_dealers(client, max_pages=1))

    assert [r.dealer_id for r in results] == ["d1"]


def test_iter_dealers_max_pages_zero_yields_nothing() -> None:
    client = FakeSyncClient([], [])
    results = list(iter_dealers(client, max_pages=0))
    assert results == []
    assert client.dealer_calls == []


def test_iter_dealers_does_not_mutate_original_filter() -> None:
    page1 = _dealers_page([_dealer("d1")], next_offset=2)
    page2 = _dealers_page([_dealer("d2")], next_offset=None, offset=2)
    client = FakeSyncClient([], [page1, page2])

    original = DealerFilter(offset=0, state=["CA"])
    list(iter_dealers(client, original))

    assert original.offset == 0


def test_iter_dealers_none_filter_uses_defaults() -> None:
    page = _dealers_page([_dealer("d1")], next_offset=None)
    client = FakeSyncClient([], [page])

    list(iter_dealers(client, None))

    assert client.dealer_calls[0] == DealerFilter()
