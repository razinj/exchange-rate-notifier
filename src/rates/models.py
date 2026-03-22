"""Models for exchange rate provider details and aggregation results."""

import typing as t
from dataclasses import dataclass, field


@dataclass(slots=True)
class RateDetail:
    """Normalized details from a single exchange rate source."""

    source: str
    pair: str
    status: str
    rate: t.Optional[float] = None
    error: t.Optional[str] = None
    metadata: t.Dict[str, t.Any] = field(default_factory=dict)


@dataclass(slots=True)
class AggregatedRateResult:
    """Final aggregated exchange rate result across all sources."""

    pair: str
    aggregation_method: str
    aggregated_rate: float
    details: t.List[RateDetail]
    successful_sources: int
    failed_sources: int
