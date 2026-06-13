import pytest

from visor import FacetsFilter, VisorClient
from visor.models.facets import FacetsResponse

pytestmark = [pytest.mark.integration, pytest.mark.release_gate]


def test_facets_basic(client: VisorClient) -> None:
    result = client.filter_facets(FacetsFilter(facets=["make", "body_type"]))
    assert isinstance(result, FacetsResponse)
    assert result.data.total > 0
    assert "make" in result.data.facets
    assert "body_type" in result.data.facets
    assert len(result.data.facets["make"]) > 0


def test_facets_with_range_facet(client: VisorClient) -> None:
    result = client.filter_facets(FacetsFilter(facets=["price", "make"]))
    assert "price" in result.data.range_facets
    assert result.data.range_facets["price"].min >= 0
    assert result.data.range_facets["price"].max > 0


def test_facets_with_filter(client: VisorClient) -> None:
    national = client.filter_facets(FacetsFilter(facets=["state"]))
    texas_only = client.filter_facets(FacetsFilter(facets=["make"], state=["TX"]))
    assert national.data.total > texas_only.data.total
