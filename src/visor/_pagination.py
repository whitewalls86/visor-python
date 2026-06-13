from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from typing import Protocol

from visor.models.dealers import DealerFilter, DealersPage, DealerSummary
from visor.models.listings import ListingsFilter, ListingsPage, ListingSummary


class _AsyncVisorClientProto(Protocol):
    async def filter_listings(
        self, filter: ListingsFilter | None = None
    ) -> ListingsPage: ...

    async def search_dealers(
        self, filter: DealerFilter | None = None
    ) -> DealersPage: ...


class _SyncVisorClientProto(Protocol):
    def filter_listings(self, filter: ListingsFilter | None = None) -> ListingsPage: ...

    def search_dealers(self, filter: DealerFilter | None = None) -> DealersPage: ...


async def paginate_listings(
    client: _AsyncVisorClientProto,
    filter: ListingsFilter | None = None,
    *,
    max_pages: int | None = None,
) -> AsyncGenerator[ListingSummary, None]:
    if max_pages is not None and max_pages <= 0:
        return
    current = filter if filter is not None else ListingsFilter()
    pages_fetched = 0
    while True:
        page = await client.filter_listings(current)
        for item in page.data:
            yield item
        pages_fetched += 1
        if max_pages is not None and pages_fetched >= max_pages:
            break
        if page.pagination.next_offset is None:
            break
        current = current.model_copy(update={"offset": page.pagination.next_offset})


async def paginate_dealers(
    client: _AsyncVisorClientProto,
    filter: DealerFilter | None = None,
    *,
    max_pages: int | None = None,
) -> AsyncGenerator[DealerSummary, None]:
    if max_pages is not None and max_pages <= 0:
        return
    current = filter if filter is not None else DealerFilter()
    pages_fetched = 0
    while True:
        page = await client.search_dealers(current)
        for item in page.data:
            yield item
        pages_fetched += 1
        if max_pages is not None and pages_fetched >= max_pages:
            break
        if page.pagination.next_offset is None:
            break
        current = current.model_copy(update={"offset": page.pagination.next_offset})


def iter_listings(
    client: _SyncVisorClientProto,
    filter: ListingsFilter | None = None,
    *,
    max_pages: int | None = None,
) -> Generator[ListingSummary, None, None]:
    if max_pages is not None and max_pages <= 0:
        return
    current = filter if filter is not None else ListingsFilter()
    pages_fetched = 0
    while True:
        page = client.filter_listings(current)
        yield from page.data
        pages_fetched += 1
        if max_pages is not None and pages_fetched >= max_pages:
            break
        if page.pagination.next_offset is None:
            break
        current = current.model_copy(update={"offset": page.pagination.next_offset})


def iter_dealers(
    client: _SyncVisorClientProto,
    filter: DealerFilter | None = None,
    *,
    max_pages: int | None = None,
) -> Generator[DealerSummary, None, None]:
    if max_pages is not None and max_pages <= 0:
        return
    current = filter if filter is not None else DealerFilter()
    pages_fetched = 0
    while True:
        page = client.search_dealers(current)
        yield from page.data
        pages_fetched += 1
        if max_pages is not None and pages_fetched >= max_pages:
            break
        if page.pagination.next_offset is None:
            break
        current = current.model_copy(update={"offset": page.pagination.next_offset})
