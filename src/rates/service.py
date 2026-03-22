"""Orchestration layer for multi-provider exchange rates."""

import os
import typing as t
from concurrent.futures import Future, ThreadPoolExecutor

from rates.aggregation import SUPPORTED_AGGREGATION_METHODS, aggregate_rates
from rates.http_client import safe_error_message
from rates.models import AggregatedRateResult, RateDetail
from rates.providers import (
    ApilayerExchangeRatesApiProvider,
    BankAlMaghribProvider,
    CurrencyApiProvider,
    ExchangeRateApiProvider,
    FawazAhmed0ExchangeApiProvider,
    OpenExchangeRatesProvider,
)
from rates.providers.base import ExchangeRateProvider

ProviderFactory = t.Callable[[], ExchangeRateProvider]

AVAILABLE_PROVIDERS: t.Dict[str, ProviderFactory] = {
    "openexchangerates": OpenExchangeRatesProvider,
    "bank_al_maghrib": BankAlMaghribProvider,
    "exchangerate_api": ExchangeRateApiProvider,
    "currencyapi": CurrencyApiProvider,
    "apilayer_exchangeratesapi": ApilayerExchangeRatesApiProvider,
    "fawazahmed0_exchange_api": FawazAhmed0ExchangeApiProvider,
}


def validate_min_successful_sources(
    min_successful_sources: int,
    provider_names: t.Sequence[str],
) -> None:
    """Ensure min successful source requirement is achievable."""
    provider_count = len(provider_names)
    if min_successful_sources > provider_count:
        raise ValueError(
            "MIN_SUCCESSFUL_SOURCES cannot be greater than number of enabled sources "
            f"(required: {min_successful_sources}, enabled: {provider_count})"
        )


def get_enabled_provider_names() -> t.List[str]:
    """Read and validate enabled provider names from env."""
    configured = os.environ.get("RATE_SOURCES", "openexchangerates")
    provider_names = [
        name.strip().lower() for name in configured.split(",") if name.strip()
    ]

    if not provider_names:
        raise ValueError("RATE_SOURCES must contain at least one provider")

    deduplicated_provider_names: t.List[str] = []
    seen_provider_names: t.Set[str] = set()
    for provider_name in provider_names:
        if provider_name in seen_provider_names:
            continue

        seen_provider_names.add(provider_name)
        deduplicated_provider_names.append(provider_name)

    unknown_names = [
        name for name in deduplicated_provider_names if name not in AVAILABLE_PROVIDERS
    ]
    if unknown_names:
        raise ValueError(
            f"Unknown provider(s): {unknown_names}. Available providers: {sorted(AVAILABLE_PROVIDERS.keys())}"
        )

    return deduplicated_provider_names


def get_aggregation_method() -> str:
    """Read and validate aggregation method from env."""
    method = os.environ.get("AGGREGATION_METHOD", "median").strip().lower()

    if method not in SUPPORTED_AGGREGATION_METHODS:
        raise ValueError(
            f"AGGREGATION_METHOD must be one of {sorted(SUPPORTED_AGGREGATION_METHODS)}, got '{method}'"
        )

    return method


def get_min_successful_sources() -> int:
    """Read and validate minimum successful source count from env."""
    raw_value = os.environ.get("MIN_SUCCESSFUL_SOURCES", "1").strip()

    if not raw_value:
        raise ValueError("MIN_SUCCESSFUL_SOURCES cannot be empty")

    min_successful_sources = int(raw_value)
    if min_successful_sources <= 0:
        raise ValueError("MIN_SUCCESSFUL_SOURCES must be a positive integer")

    return min_successful_sources


def fetch_rate_details(
    base_currency: str,
    quote_currency: str,
    provider_names: t.Optional[t.Sequence[str]] = None,
) -> t.List[RateDetail]:
    """Fetch normalized rate details from all selected providers."""
    selected_provider_names = (
        list(provider_names) if provider_names else get_enabled_provider_names()
    )

    if not selected_provider_names:
        return []

    details: t.List[RateDetail] = []
    futures: t.List[Future[RateDetail]] = []

    max_workers = min(len(selected_provider_names), 8)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for provider_name in selected_provider_names:
            provider_factory = AVAILABLE_PROVIDERS[provider_name]
            provider = provider_factory()
            futures.append(
                executor.submit(provider.fetch_rate, base_currency, quote_currency)
            )

        for provider_name, future in zip(selected_provider_names, futures):
            try:
                details.append(future.result())
            except Exception as error:  # pragma: no cover - defensive fallback
                details.append(
                    RateDetail(
                        source=provider_name,
                        pair=f"{base_currency}/{quote_currency}",
                        status="error",
                        error=f"Unhandled provider failure: {safe_error_message(error)}",
                    )
                )

    return details


def aggregate_rate_details(
    base_currency: str,
    quote_currency: str,
    details: t.Sequence[RateDetail],
    aggregation_method: str,
    min_successful_sources: int,
) -> AggregatedRateResult:
    """Aggregate normalized provider details into one final rate."""
    successful_rates = [
        detail.rate
        for detail in details
        if detail.status == "success" and detail.rate is not None
    ]
    successful_rates_as_float = [float(rate) for rate in successful_rates]

    if len(successful_rates_as_float) < min_successful_sources:
        raise ValueError(
            "Not enough successful sources to aggregate "
            f"(required: {min_successful_sources}, available: {len(successful_rates_as_float)})"
        )

    final_rate = aggregate_rates(successful_rates_as_float, aggregation_method)
    pair = f"{base_currency}/{quote_currency}"

    return AggregatedRateResult(
        pair=pair,
        aggregation_method=aggregation_method,
        aggregated_rate=final_rate,
        details=list(details),
        successful_sources=len(successful_rates_as_float),
        failed_sources=len(details) - len(successful_rates_as_float),
    )


def fetch_and_aggregate_rate(
    base_currency: str,
    quote_currency: str,
    aggregation_method: t.Optional[str] = None,
    provider_names: t.Optional[t.Sequence[str]] = None,
    min_successful_sources: t.Optional[int] = None,
) -> AggregatedRateResult:
    """Convenience helper to fetch provider details and aggregate them."""
    method = (
        aggregation_method
        if aggregation_method is not None
        else get_aggregation_method()
    )
    min_successful = (
        min_successful_sources
        if min_successful_sources is not None
        else get_min_successful_sources()
    )
    selected_provider_names = (
        list(provider_names)
        if provider_names is not None
        else get_enabled_provider_names()
    )

    validate_min_successful_sources(min_successful, selected_provider_names)

    details = fetch_rate_details(
        base_currency=base_currency,
        quote_currency=quote_currency,
        provider_names=selected_provider_names,
    )

    return aggregate_rate_details(
        base_currency=base_currency,
        quote_currency=quote_currency,
        details=details,
        aggregation_method=method,
        min_successful_sources=min_successful,
    )
