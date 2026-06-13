import pytest

from visor import (
    AuthError,
    ForbiddenError,
    NotFoundError,
    VisorAPIError,
    VisorClient,
    VisorTransportError,
)

pytestmark = pytest.mark.integration


@pytest.mark.release_gate
def test_auth_error_bad_key() -> None:
    # Live invalid-key behavior varies: the API itself may return 401 AuthError,
    # or the Cloudflare WAF layer may intercept first and return 403 ForbiddenError.
    # Both are correct SDK behavior; assert the response is one of the two.
    with (
        VisorClient(api_key="vsr_live_thisisnotarealkey") as bad_client,
        pytest.raises((AuthError, ForbiddenError)) as exc_info,
    ):
        bad_client.filter_listings()
    exc = exc_info.value
    assert exc.status_code in (401, 403)
    assert exc.message
    assert str(exc.status_code) in str(exc)


@pytest.mark.release_gate
def test_not_found_listing(client: VisorClient) -> None:
    # Live API may return 404 NotFoundError or 503 VisorAPIError (data_unavailable)
    # for non-existent listing IDs.  Both are acceptable; the SDK maps them correctly.
    with pytest.raises(VisorAPIError) as exc_info:
        client.get_listing("00000000000000000000000000000000")
    exc = exc_info.value
    assert exc.status_code in (404, 503)
    if exc.status_code == 503:
        assert exc.error_code == "data_unavailable"


@pytest.mark.release_gate
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
