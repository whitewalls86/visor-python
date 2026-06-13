import asyncio
import functools
import os
import threading
import time
from typing import Any

import pytest
import pytest_asyncio

from visor import AsyncVisorClient, VisorClient
from visor.exceptions import RateLimitError

# ---------------------------------------------------------------------------
# Live-request throttle
# Applied to the transport layer of every integration client to prevent
# exhausting the per-key rate limit mid-suite.  Controlled via
# VISOR_INTEGRATION_MIN_INTERVAL_SECONDS (default 10.5 s).
# ---------------------------------------------------------------------------

_last_request_time: float = 0.0
_request_lock = threading.Lock()


def _min_interval() -> float:
    try:
        return float(os.environ.get("VISOR_INTEGRATION_MIN_INTERVAL_SECONDS", "10.5"))
    except ValueError:
        return 10.5


def _throttle_sync(fn: Any) -> Any:
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        global _last_request_time
        interval = _min_interval()
        with _request_lock:
            now = time.monotonic()
            wait = max(0.0, _last_request_time + interval - now)
            _last_request_time = now + wait
        if wait:
            time.sleep(wait)
        try:
            return fn(*args, **kwargs)
        except RateLimitError as exc:
            delay = exc.retry_after if exc.retry_after is not None else interval
            time.sleep(delay)
            with _request_lock:
                _last_request_time = time.monotonic()
            return fn(*args, **kwargs)

    return wrapper


def _throttle_async(fn: Any) -> Any:
    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        global _last_request_time
        interval = _min_interval()
        with _request_lock:
            now = time.monotonic()
            wait = max(0.0, _last_request_time + interval - now)
            _last_request_time = now + wait
        if wait:
            await asyncio.sleep(wait)
        try:
            return await fn(*args, **kwargs)
        except RateLimitError as exc:
            delay = exc.retry_after if exc.retry_after is not None else interval
            await asyncio.sleep(delay)
            with _request_lock:
                _last_request_time = time.monotonic()
            return await fn(*args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------------
# Pytest configuration
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def api_key() -> str:
    key = os.environ.get("VISOR_API_KEY")
    if not key:
        pytest.skip("VISOR_API_KEY not set — skipping integration tests")
    return key


@pytest.fixture(scope="session")
def client(api_key: str) -> VisorClient:
    with VisorClient(api_key=api_key) as c:
        c._transport.get = _throttle_sync(c._transport.get)  # type: ignore[method-assign]
        yield c  # type: ignore[misc]


@pytest_asyncio.fixture
async def async_client(api_key: str) -> AsyncVisorClient:
    async with AsyncVisorClient(api_key=api_key) as c:
        c._transport.get = _throttle_async(c._transport.get)  # type: ignore[method-assign]
        yield c  # type: ignore[misc]


@pytest.fixture(scope="session")
def _sample_listing(client: VisorClient) -> Any:
    from visor import ListingsFilter

    page = client.filter_listings(ListingsFilter(limit=1))
    assert page.data, "No listings returned — cannot run integration tests"
    return page.data[0]


@pytest.fixture(scope="session")
def sample_listing_id(_sample_listing: Any) -> str:
    return str(_sample_listing.id)


@pytest.fixture(scope="session")
def sample_vin(_sample_listing: Any) -> str:
    return str(_sample_listing.vin)


@pytest.fixture(scope="session")
def sample_dealer_id(client: VisorClient) -> str:
    from visor import DealerFilter

    page = client.search_dealers(DealerFilter(limit=1))
    assert page.data, "No dealers returned — cannot run dealer integration tests"
    return page.data[0].dealer_id
