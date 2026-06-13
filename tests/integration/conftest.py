import os

import pytest
import pytest_asyncio

from visor import AsyncVisorClient, VisorClient


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "integration: mark test as requiring a live API key"
    )
    config.addinivalue_line(
        "markers", "release_gate: stable live tests required before publishing"
    )
    config.addinivalue_line(
        "markers", "manual: live tests that require special credentials/account state"
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--run-integration"):
        return
    skip_integration = pytest.mark.skip(
        reason="live integration test; pass --run-integration to run"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


@pytest.fixture(scope="session")
def api_key() -> str:
    key = os.environ.get("VISOR_API_KEY")
    if not key:
        pytest.skip("VISOR_API_KEY not set — skipping integration tests")
    return key


@pytest.fixture(scope="session")
def client(api_key: str) -> VisorClient:
    with VisorClient(api_key=api_key) as c:
        yield c  # type: ignore[misc]


@pytest_asyncio.fixture
async def async_client(api_key: str) -> AsyncVisorClient:
    async with AsyncVisorClient(api_key=api_key) as c:
        yield c  # type: ignore[misc]


@pytest.fixture(scope="session")
def sample_listing_id(client: VisorClient) -> str:
    from visor import ListingsFilter

    page = client.filter_listings(ListingsFilter(limit=1))
    assert page.data, "No listings returned — cannot run integration tests"
    return page.data[0].id


@pytest.fixture(scope="session")
def sample_vin(client: VisorClient) -> str:
    from visor import ListingsFilter

    page = client.filter_listings(ListingsFilter(limit=1))
    assert page.data
    return page.data[0].vin


@pytest.fixture(scope="session")
def sample_dealer_id(client: VisorClient) -> str:
    from visor import DealerFilter

    page = client.search_dealers(DealerFilter(limit=1))
    assert page.data, "No dealers returned — cannot run dealer integration tests"
    return page.data[0].dealer_id
