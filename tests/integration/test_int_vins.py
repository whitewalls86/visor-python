import pytest

from visor import NotFoundError, VisorClient
from visor.models.vins import VinDetail

pytestmark = [pytest.mark.integration, pytest.mark.release_gate]


def test_lookup_vin_from_search(client: VisorClient, sample_vin: str) -> None:
    result = client.lookup_vin(sample_vin)
    assert isinstance(result, VinDetail)
    assert result.vin == sample_vin
    assert result.status in ("active", "missing", "sold")
    assert result.build is not None
    assert result.build.make is not None
    assert result.build.year is not None


def test_lookup_vin_with_price_history(client: VisorClient, sample_vin: str) -> None:
    result = client.lookup_vin(sample_vin, include=["price_history"])
    assert isinstance(result, VinDetail)
    if result.latest_listing:
        assert isinstance(result.latest_listing.price_history, list)


def test_lookup_vin_with_options(client: VisorClient, sample_vin: str) -> None:
    result = client.lookup_vin(sample_vin, include=["options"])
    assert isinstance(result, VinDetail)
    assert isinstance(result.build.options, list)


def test_lookup_vin_not_found(client: VisorClient) -> None:
    with pytest.raises(NotFoundError) as exc_info:
        client.lookup_vin("ZZZZZZZZZZZZZZZZZ")
    assert exc_info.value.status_code == 404
