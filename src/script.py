import os
import typing as t

import httpx
from dotenv import load_dotenv

from email_client import send_email_mg  # type: ignore

load_dotenv()

OER_APP_ID = os.getenv("OER_APP_ID")
TARGET_CURRENCY = os.getenv("TARGET_CURRENCY")
COMPARISON_CURRENCY = os.getenv("COMPARISON_CURRENCY")
THRESHOLD_RATE = os.getenv("THRESHOLD_RATE")


def send_email(content: str, current_exchange_rate: float) -> None:
    target_currency = TARGET_CURRENCY.upper() if TARGET_CURRENCY else ""
    comparison_currency = COMPARISON_CURRENCY.upper() if COMPARISON_CURRENCY else ""
    threshold_rate = float(THRESHOLD_RATE) if THRESHOLD_RATE else 0
    subject = f"{target_currency}/{comparison_currency} - Current exchange rate {current_exchange_rate:.2f} is above threshold {threshold_rate:.2f}"  # noqa: E501

    send_email_mg(subject, content)


def fetch_exchange_rates() -> t.Dict[str, t.Any]:
    if not OER_APP_ID:
        raise ValueError("OER_APP_ID is required")

    api_url = "https://openexchangerates.org/api/latest.json"
    params = {"app_id": OER_APP_ID}
    response = httpx.get(api_url, params=params)

    response.raise_for_status()

    return response.json()


def prepare_inputs() -> t.Tuple[float, str, str]:
    if not THRESHOLD_RATE or not TARGET_CURRENCY or not COMPARISON_CURRENCY:
        raise ValueError("Rate and currencies are required")

    if len(TARGET_CURRENCY) != 3 or len(COMPARISON_CURRENCY) != 3:
        raise ValueError("Currencies should be exactly 3 characters long")

    if float(THRESHOLD_RATE) < 0:
        raise ValueError("Threshold should be a positive number")

    return float(THRESHOLD_RATE), TARGET_CURRENCY.upper(), COMPARISON_CURRENCY.upper()


def check_and_notify(
    exchange_rates: t.Dict[str, t.Any],
    threshold_rate: float,
    target_currency: str,
    comparison_currency: str,
) -> None:
    # Get the rates for the target and comparison currencies againts the base currency (USD)  # noqa: E501
    usd_to_target_currency = exchange_rates["rates"][target_currency]
    usd_to_comparison_currency = exchange_rates["rates"][comparison_currency]

    # Calculate the cross rate
    target_to_comparison_currency = usd_to_target_currency / usd_to_comparison_currency

    print(
        f"Calculated {comparison_currency} to {target_currency} rate is {target_to_comparison_currency:.2f}"  # noqa: E501
    )

    if target_to_comparison_currency >= threshold_rate:
        message = f"The current exchange rate {target_to_comparison_currency:.2f} {target_currency} is equal to or higher than the threshold rate {threshold_rate:.2f} {target_currency}."  # noqa: E501
        print(message)
        send_email_mg(message, target_to_comparison_currency)
    else:
        print(
            f"The current exchange rate {target_to_comparison_currency:.2f} {target_currency} is below the threshold rate {threshold_rate:.2f} {target_currency}."  # noqa: E501
        )


if __name__ == "__main__":
    threshold_rate, target_currency, comparison_currency = prepare_inputs()
    exchange_rates = fetch_exchange_rates()
    check_and_notify(
        exchange_rates, threshold_rate, target_currency, comparison_currency
    )
