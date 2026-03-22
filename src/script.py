import os
import typing as t

from dotenv import load_dotenv

from notifications import notify
from rates.models import RateDetail
from rates.service import (
    aggregate_rate_details,
    fetch_rate_details,
    get_aggregation_method,
    get_enabled_provider_names,
    get_min_successful_sources,
    validate_min_successful_sources,
)

load_dotenv()


def prepare_inputs() -> t.Tuple[float, str, str]:
    threshold_rate = os.environ["THRESHOLD_RATE"]
    base_currency = _read_required_env("BASE_CURRENCY")
    quote_currency = _read_required_env("QUOTE_CURRENCY")

    if float(threshold_rate) < 0:
        raise ValueError("Threshold should be a positive number")

    return float(threshold_rate), base_currency.upper(), quote_currency.upper()


def _read_required_env(env_var: str) -> str:
    value = os.environ.get(env_var, "").strip()
    if value:
        return value

    raise ValueError(f"{env_var} is required")


def _read_bool_env(env_var: str, default: bool = False) -> bool:
    raw_value = os.environ.get(env_var)
    if raw_value is None:
        return default

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True

    if normalized in {"0", "false", "no", "n", "off"}:
        return False

    raise ValueError(
        f"{env_var} must be a boolean value (true/false/1/0/yes/no), got '{raw_value}'"
    )


def _format_rate_detail(detail: RateDetail) -> str:
    if detail.status == "success" and detail.rate is not None:
        return f"[{detail.source}] {detail.pair}={detail.rate:.4f}"

    error_message = detail.error or "Unknown error"
    return f"[{detail.source}] {detail.status}: {error_message}"


def _format_details_block(details: t.Sequence[RateDetail]) -> str:
    return "\n".join(f"- {_format_rate_detail(detail)}" for detail in details)


def check_and_notify() -> None:
    threshold_rate, base_currency, quote_currency = prepare_inputs()
    aggregation_method = get_aggregation_method()
    provider_names = get_enabled_provider_names()
    min_successful_sources = get_min_successful_sources()
    notify_on_aggregation_failure = _read_bool_env(
        "NOTIFY_ON_AGGREGATION_FAILURE", default=True
    )

    validate_min_successful_sources(min_successful_sources, provider_names)

    details = fetch_rate_details(
        base_currency=base_currency,
        quote_currency=quote_currency,
        provider_names=provider_names,
    )

    try:
        result = aggregate_rate_details(
            base_currency=base_currency,
            quote_currency=quote_currency,
            details=details,
            aggregation_method=aggregation_method,
            min_successful_sources=min_successful_sources,
        )
    except ValueError as error:
        print("Details:")
        print(_format_details_block(details))

        if notify_on_aggregation_failure:
            subject = f"{base_currency}/{quote_currency} - Aggregation failed"
            message = (
                f"Failed to aggregate exchange rate for {base_currency}/{quote_currency}.\n"
                f"Reason: {error}\n"
                f"Source details:\n{_format_details_block(details)}"
            )
            notify(subject, message)

        raise

    print(
        f"Calculated {result.pair} rate is {result.aggregated_rate:.4f} "
        f"using {result.aggregation_method} from "
        f"{result.successful_sources}/{len(result.details)} source(s)."
    )

    print("Details:")
    print(_format_details_block(result.details))

    details_block = _format_details_block(result.details)

    if result.aggregated_rate >= threshold_rate:
        message = (
            f"The current {result.pair} exchange rate is {result.aggregated_rate:.4f}, "
            f"which is equal to or higher than the threshold rate {threshold_rate:.4f}. "
            f"Aggregation method: {result.aggregation_method}.\n"
            f"Source details:\n{details_block}"
        )
        subject = (
            f"{result.pair} - Aggregated rate {result.aggregated_rate:.4f} "
            f"is above threshold {threshold_rate:.4f}"
        )

        print(message)
        notify(subject, message)
    else:
        print(
            f"The current {result.pair} exchange rate is {result.aggregated_rate:.4f}, "
            f"which is below the threshold rate {threshold_rate:.4f}."
        )


if __name__ == "__main__":
    check_and_notify()
