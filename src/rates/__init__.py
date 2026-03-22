"""Rates package for provider adapters and aggregation orchestration."""

from rates.models import AggregatedRateResult, RateDetail
from rates.service import (
    aggregate_rate_details,
    fetch_and_aggregate_rate,
    fetch_rate_details,
    get_aggregation_method,
    get_enabled_provider_names,
    get_min_successful_sources,
    validate_min_successful_sources,
)

__all__ = [
    "AggregatedRateResult",
    "RateDetail",
    "aggregate_rate_details",
    "fetch_and_aggregate_rate",
    "fetch_rate_details",
    "get_aggregation_method",
    "get_enabled_provider_names",
    "get_min_successful_sources",
    "validate_min_successful_sources",
]
