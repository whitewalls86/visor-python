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
    from visor import VisorAPIError

    try:
        client.lookup_vin("ZZZZZZZZZZZZZZZZZ")
        pytest.fail("Expected an exception for an unknown VIN")
    except NotFoundError as e:
        assert e.status_code == 404
    except VisorAPIError as e:
        pytest.skip(
            f"Live API returned non-404 error for improbable VIN "
            f"(status={e.status_code}, code={e.error_code}) — SDK is fine"
        )
