from datetime import date

from visor.models._base import VisorResponseModel


class UsageRecord(VisorResponseModel):
    date: date
    metering_class: str
    requests: int
    charged_micros: int


class UsageTotals(VisorResponseModel):
    requests: int
    charged_micros: int


class UsageMeta(VisorResponseModel):
    start_date: date
    end_date: date
    interval: str
    currency: str
    source: str
    freshness: str


class UsageSummary(VisorResponseModel):
    data: list[UsageRecord]
    totals: UsageTotals
    meta: UsageMeta
