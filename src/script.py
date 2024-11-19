import os
import typing as t

import httpx
from dotenv import load_dotenv

load_dotenv()

OER_APP_ID = os.getenv("OER_APP_ID")
TARGET_CURRENCY = os.getenv("TARGET_CURRENCY")
COMPARISON_CURRENCY = os.getenv("COMPARISON_CURRENCY")
THRESHOLD_RATE = os.getenv("THRESHOLD_RATE")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_FROM = os.getenv("MAILGUN_FROM")
MAILGUN_TO = os.getenv("MAILGUN_TO")


def fetch_exchange_rates() -> t.Dict[str, t.Any]:
    if not OER_APP_ID:
        raise ValueError("OER_APP_ID is required")

    api_url = "https://openexchangerates.org/api/latest.json"
    params = {"app_id": OER_APP_ID}
    response = httpx.get(api_url, params=params)

    response.raise_for_status()

    return response.json()


def send_email(subject: str, content: str) -> None:
    if not MAILGUN_DOMAIN or not MAILGUN_API_KEY or not MAILGUN_FROM or not MAILGUN_TO:
        raise ValueError("All mail variables are required")

    data: t.Dict[str, str] = {
        "from": MAILGUN_FROM,
        "to": MAILGUN_TO,
        "subject": subject,
        "text": content,
    }

    response = httpx.post(
        url=f"https://api.eu.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data=data,
    )

    if response.status_code == 200:
        print("Email sent successfully!")
    else:
        print(f"Failed to send email, response: {response.text}")


def prepare_inputs() -> t.Tuple[float, str, str]:
    if not THRESHOLD_RATE or not TARGET_CURRENCY or not COMPARISON_CURRENCY:
        raise ValueError("Rate and currencies are required")

    if float(THRESHOLD_RATE) < 0:
        raise ValueError("Threshold should be a positive number")

    return float(THRESHOLD_RATE), TARGET_CURRENCY.upper(), COMPARISON_CURRENCY.upper()


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
        send_email(subject, message)
    else:
        print(
            f"The current exchange rate {target_to_comparison_currency:.2f} {target_currency} is below the threshold rate {threshold_rate:.2f} {target_currency}."  # noqa: E501
        )


if __name__ == "__main__":
    check_and_notify()
