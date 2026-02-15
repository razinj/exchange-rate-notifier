import os
import typing as t

import httpx
from dotenv import load_dotenv

from notifications import notify

load_dotenv()


def fetch_exchange_rates() -> t.Dict[str, t.Any]:
    api_url = "https://openexchangerates.org/api/latest.json"
    params = {"app_id": os.environ["OER_APP_ID"]}
    response = httpx.get(api_url, params=params)

    response.raise_for_status()

    return t.cast(t.Dict[str, t.Any], response.json())


def prepare_inputs() -> t.Tuple[float, str, str]:
    threshold_rate = os.environ["THRESHOLD_RATE"]
    target_currency = os.environ["TARGET_CURRENCY"]
    comparison_currency = os.environ["COMPARISON_CURRENCY"]

    if float(threshold_rate) < 0:
        raise ValueError("Threshold should be a positive number")

    return float(threshold_rate), target_currency.upper(), comparison_currency.upper()


def check_and_notify() -> None:
    exchange_rates = fetch_exchange_rates()
    threshold_rate, target_currency, comparison_currency = prepare_inputs()

    # Get the rates for the target and comparison currencies againts the base currency (USD)
    usd_to_target_currency = exchange_rates["rates"][target_currency]
    usd_to_comparison_currency = exchange_rates["rates"][comparison_currency]

    # Calculate the cross rate
    target_to_comparison_currency = usd_to_target_currency / usd_to_comparison_currency

    print(
        f"Calculated {comparison_currency} to {target_currency} rate is {target_to_comparison_currency:.2f}"
    )

    if target_to_comparison_currency >= threshold_rate:
        message = f"The current exchange rate {target_to_comparison_currency:.2f} {target_currency} is equal to or higher than the threshold rate {threshold_rate:.2f} {target_currency}."  # noqa: E501
        subject = f"{target_currency}/{comparison_currency} - Current exchange rate {target_to_comparison_currency:.2f} is above threshold {threshold_rate:.2f}"  # noqa: E501

        print(message)
        notify(subject, message)
    else:
        print(
            f"The current exchange rate {target_to_comparison_currency:.2f} {target_currency} is below the threshold rate {threshold_rate:.2f} {target_currency}."  # noqa: E501
        )


if __name__ == "__main__":
    check_and_notify()
