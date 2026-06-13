from visor._client import AsyncVisorClient
from visor._pagination import (
    iter_dealers,
    iter_listings,
    paginate_dealers,
    paginate_listings,
)
from visor.exceptions import (
    AuthError,
    ForbiddenError,
    NotFoundError,
    PaymentRequiredError,
    RateLimitError,
    ValidationError,
    VisorAPIError,
    VisorError,
    VisorTransportError,
)
from visor.models._base import (
    BBox,
    DealerRef,
    Pagination,
    VehicleBuild,
    VehicleOption,
    VehicleRecord,
)
from visor.models.dealers import (
    DealerAddress,
    DealerDetail,
    DealerFilter,
    DealersPage,
    DealerSummary,
)
from visor.models.facets import FacetBucket, FacetsData, FacetsFilter, FacetsResponse
from visor.models.listings import (
    ListingDetail,
    ListingsFilter,
    ListingSnapshot,
    ListingsPage,
    ListingSummary,
)
from visor.models.usage import UsageMeta, UsageRecord, UsageSummary, UsageTotals
from visor.models.vins import VinDetail

__all__ = [
    # client
    "AsyncVisorClient",
    # pagination
    "paginate_listings",
    "paginate_dealers",
    "iter_listings",
    "iter_dealers",
    # exceptions
    "AuthError",
    "ForbiddenError",
    "NotFoundError",
    "PaymentRequiredError",
    "RateLimitError",
    "ValidationError",
    "VisorAPIError",
    "VisorError",
    "VisorTransportError",
    # shared base
    "BBox",
    "DealerRef",
    "Pagination",
    "VehicleBuild",
    "VehicleOption",
    "VehicleRecord",
    # dealers
    "DealerAddress",
    "DealerDetail",
    "DealerFilter",
    "DealersPage",
    "DealerSummary",
    # facets
    "FacetBucket",
    "FacetsData",
    "FacetsFilter",
    "FacetsResponse",
    # listings
    "ListingDetail",
    "ListingsFilter",
    "ListingsPage",
    "ListingSnapshot",
    "ListingSummary",
    # usage
    "UsageMeta",
    "UsageRecord",
    "UsageSummary",
    "UsageTotals",
    # vins
    "VinDetail",
]
