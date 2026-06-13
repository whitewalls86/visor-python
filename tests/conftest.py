import httpx
import pytest
import respx


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run live Visor API integration tests",
    )


API_BASE = "https://api.visor.vin/v1"


@pytest.fixture
def mock_transport() -> respx.MockRouter:
    with respx.mock(base_url=API_BASE) as mock:
        yield mock


# Sample API responses — match actual API response shapes exactly

LISTING_SUMMARY = {
    "id": "0043554b54709f18a7bcf42f23e5e6ef",
    "vin": "4T1DAACKXTU765422",
    "year": 2026,
    "make": "Toyota",
    "model": "Camry",
    "trim": "SE",
    "price": 35236,
    "miles": 0,
    "status": "active",
    "inventory_status": "active",
    "inventory_type": "new",
    "dealer_id": "16ed7612-0ffd-4e1e-88db-174f8dd57c54",
    "dealer_name": "North Hollywood Toyota",
    "city": "North Hollywood",
    "state": "CA",
    "vdp_url": "https://www.northhollywoodtoyota.com/viewdetails/new/4t1daackxtu765422",
}

PAGINATION_ONE_PAGE = {"limit": 50, "offset": 0, "total": 1, "next_offset": None}
PAGINATION_TWO_PAGES = {"limit": 2, "offset": 0, "total": 4, "next_offset": 2}

# Keep httpx importable from conftest for test files that need it
__all__ = [
    "API_BASE",
    "LISTING_SUMMARY",
    "PAGINATION_ONE_PAGE",
    "PAGINATION_TWO_PAGES",
    "httpx",
    "mock_transport",
]
