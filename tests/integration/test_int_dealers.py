import pytest

from visor import DealerFilter, VisorClient
from visor.models.dealers import DealerDetail, DealersPage
from visor.models.listings import ListingsPage

pytestmark = [pytest.mark.integration, pytest.mark.release_gate]


def test_search_dealers_default(client: VisorClient) -> None:
    page = client.search_dealers()
    assert isinstance(page, DealersPage)
    assert len(page.data) > 0
    assert page.pagination.total > 0


def test_search_dealers_by_state(client: VisorClient) -> None:
    page = client.search_dealers(DealerFilter(state=["TX"], limit=5))
    assert len(page.data) > 0
    for dealer in page.data:
        assert dealer.state == "TX"


def test_get_dealer(client: VisorClient, sample_dealer_id: str) -> None:
    dealer = client.get_dealer(sample_dealer_id)
    assert isinstance(dealer, DealerDetail)
    assert dealer.dealer_id == sample_dealer_id
    assert dealer.name is not None
    assert dealer.city is not None
    assert dealer.state is not None


def test_dealer_inventory(client: VisorClient, sample_dealer_id: str) -> None:
    page = client.dealer_inventory(sample_dealer_id)
    assert isinstance(page, ListingsPage)
    assert page.pagination is not None
