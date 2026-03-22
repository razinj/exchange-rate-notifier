"""Aggregation helpers for multiple exchange rate values."""

import typing as t
from statistics import mean, median

SUPPORTED_AGGREGATION_METHODS = {"median", "mean"}


def aggregate_rates(rates: t.List[float], method: str) -> float:
    """Aggregate rates using the selected method."""
    if not rates:
        raise ValueError("At least one successful rate is required for aggregation")

    normalized_method = method.strip().lower()

    if normalized_method == "median":
        return float(median(rates))

    if normalized_method == "mean":
        return float(mean(rates))

    raise ValueError(
        f"Unsupported aggregation method '{method}'. Supported methods: {sorted(SUPPORTED_AGGREGATION_METHODS)}"
    )
