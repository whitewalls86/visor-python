from visor.models._base import VehicleBuild, VisorResponseModel
from visor.models.listings import ListingSnapshot


class VinDetail(VisorResponseModel):
    vin: str
    status: str
    build: VehicleBuild
    latest_listing: ListingSnapshot | None = None
