import pytest

from visor import (
    AsyncVisorClient,
    DealerFilter,
    ListingsFilter,
    VisorClient,
    iter_dealers,
    iter_listings,
    paginate_listings,
)

pytestmark = [pytest.mark.integration, pytest.mark.release_gate]


def test_iter_listings_two_pages(client: VisorClient) -> None:
    one_page = client.filter_listings(ListingsFilter(limit=10))
    if one_page.pagination.next_offset is None:
        pytest.skip("Fewer than 10 total results — cannot test pagination")

    two_pages = list(iter_listings(client, ListingsFilter(limit=10), max_pages=2))
    assert 10 < len(two_pages) <= 20


def test_iter_dealers_default(client: VisorClient) -> None:
    results = list(iter_dealers(client, DealerFilter(limit=5), max_pages=2))
    assert len(results) > 0


def test_pagination_filter_not_mutated(client: VisorClient) -> None:
    f = ListingsFilter(make=["Toyota"], limit=5, offset=0)
    original_offset = f.offset
    list(iter_listings(client, f, max_pages=2))
    assert f.offset == original_offset


@pytest.mark.asyncio
async def test_async_listings_smoke(async_client: AsyncVisorClient) -> None:
    from visor.models.listings import ListingSummary

    results = []
    async for listing in paginate_listings(
        async_client, ListingsFilter(limit=5), max_pages=1
    ):
        results.append(listing)
    assert 0 < len(results) <= 5
    for item in results:
        assert isinstance(item, ListingSummary)
