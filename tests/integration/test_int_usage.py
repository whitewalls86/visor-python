from datetime import date, timedelta

import pytest

from visor import VisorClient
from visor.models.usage import UsageSummary

pytestmark = [pytest.mark.integration, pytest.mark.release_gate]


def test_get_usage_default(client: VisorClient) -> None:
    result = client.get_usage()
    assert isinstance(result, UsageSummary)
    assert result.totals.requests >= 0
    assert result.meta.currency == "USD"
    assert result.meta.start_date <= result.meta.end_date


def test_get_usage_date_range(client: VisorClient) -> None:
    end = date.today()
    start = end - timedelta(days=7)
    result = client.get_usage(start_date=start, end_date=end)
    assert result.meta.start_date == start
    assert result.meta.end_date == end
    for record in result.data:
        assert start <= record.date <= end
