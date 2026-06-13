import pytest

from visor import AuthError, NotFoundError, VisorClient, VisorTransportError

pytestmark = [pytest.mark.integration, pytest.mark.release_gate]


def test_auth_error_bad_key() -> None:
    with (
        VisorClient(api_key="vsr_live_thisisnotarealkey") as bad_client,
        pytest.raises(AuthError) as exc_info,
    ):
        bad_client.filter_listings()
    assert exc_info.value.status_code == 401
    assert exc_info.value.error_code is not None
    assert exc_info.value.message is not None
    assert "401" in str(exc_info.value)


def test_not_found_listing(client: VisorClient) -> None:
    with pytest.raises(NotFoundError) as exc_info:
        client.get_listing("00000000000000000000000000000000")
    assert exc_info.value.status_code == 404


def test_not_found_dealer(client: VisorClient) -> None:
    with pytest.raises(NotFoundError) as exc_info:
        client.get_dealer("00000000-0000-0000-0000-000000000000")
    assert exc_info.value.status_code == 404


def test_transport_error_unreachable_host() -> None:
    with (
        VisorClient(
            api_key="test",
            base_url="https://this-host-does-not-exist.visor.vin/v1",
            timeout=2.0,
        ) as bad_client,
        pytest.raises(VisorTransportError),
    ):
        bad_client.filter_listings()
