import json
import os
import time
import typing as t
from datetime import date

import httpx
from dotenv import load_dotenv

load_dotenv()

OER_APP_ID = os.getenv("OER_APP_ID")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_FROM = os.getenv("MAILGUN_FROM")
MAILGUN_TO = os.getenv("MAILGUN_TO")
TARGET_RATE = os.getenv("TARGET_RATE")
COMPARISON_RATE = os.getenv("COMPARISON_RATE")
THRESHOLD_RATE = os.getenv("THRESHOLD_RATE")


def send_email_mg(content: str):
    if not MAILGUN_DOMAIN or not MAILGUN_API_KEY or not MAILGUN_FROM or not MAILGUN_TO:
        raise ValueError("All mail variables are required")
    if not content:
        raise ValueError("Content is required")

    today_tmp = date.today()
    target_rate_tmp = TARGET_RATE.upper() if TARGET_RATE else ""
    comp_rate_tmp = COMPARISON_RATE.upper() if COMPARISON_RATE else ""
    threshold_rate_tmp = float(THRESHOLD_RATE) if THRESHOLD_RATE else 0
    subject = f"{today_tmp} - {target_rate_tmp}/{comp_rate_tmp} - Exchange Rate above threshold ({threshold_rate_tmp:.2f})"  # noqa: E501

    # Construct the email data
    data = {
        "from": MAILGUN_FROM,
        "to": MAILGUN_TO,
        "subject": subject,
        "text": content,
    }

    # Mailgun API endpoint
    url = f"https://api.eu.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"

    # Make the request
    response = httpx.post(url, auth=("api", MAILGUN_API_KEY), data=data)

    # Check response status
    if response.status_code == 200:
        print("Email sent successfully!")
    else:
        print("Failed to send email:")
        print(response.text)


def fetch_exchange_rates() -> t.Dict[str, t.Any]:
    if not OER_APP_ID:
        raise ValueError("OER_APP_ID is required")

    api_url = "https://openexchangerates.org/api/latest.json"
    params = {"app_id": OER_APP_ID}
    response = httpx.get(api_url, params=params)

    response.raise_for_status()

    return response.json()


def prepare_inputs() -> t.Tuple[float, str, str]:
    if not THRESHOLD_RATE or not TARGET_RATE or not COMPARISON_RATE:
        raise ValueError("All inputs are required")

    if len(TARGET_RATE) != 3 or len(COMPARISON_RATE) != 3:
        raise ValueError("Exchange rate should be 3 exactly characters long")

    if float(THRESHOLD_RATE) < 0:
        raise ValueError("Threshold should be a positive number")

    return float(THRESHOLD_RATE), TARGET_RATE.upper(), COMPARISON_RATE.upper()


def calculate_cross_rate(
    base_to_target_rate: float, base_to_comparison_rate: float
) -> float:
    return base_to_target_rate / base_to_comparison_rate


def check_rate_and_notify(current_rate: float, threshold_rate: float) -> None:
    if current_rate >= threshold_rate:
        print(
            f"The current exchange rate ({current_rate:.2f}) is equal to or higher than the threshold rate ({threshold_rate:.2f}).\nData Captured on {time.strftime('%H:%M:%S')}"  # noqa: E501
        )
        send_email_mg(
            f"The current exchange rate ({current_rate:.2f}) is equal to or higher than the threshold rate ({threshold_rate:.2f}).\nData Captured on {time.strftime('%H:%M:%S')}",  # noqa: E501
        )
    else:
        print(
            f"The current exchange rate ({current_rate:.2f}) is below the threshold rate ({threshold_rate:.2f}).\nData Captured on {time.strftime('%H:%M:%S')}"  # noqa: E501
        )
        send_email_mg(
            f"The current exchange rate ({current_rate:.2f}) is below the threshold rate ({threshold_rate:.2f}).\nData Captured on {time.strftime('%H:%M:%S')}",  # noqa: E501
        )


def main(
    exchange_rates: t.Dict[str, t.Any],
    threshold_rate: float,
    target_currency: str,
    comparison_currency: str,
) -> None:
    # Get the rates for the target and comparison currencies againts the base currency    # noqa: E501
    usd_to_target_rate = exchange_rates["rates"][target_currency]
    usd_to_comparison_rate = exchange_rates["rates"][comparison_currency]

    # Calculate the cross rate
    target_to_comparison_rate = calculate_cross_rate(
        usd_to_target_rate, usd_to_comparison_rate
    )

    print(
        f"Calculated {comparison_currency} to {target_currency} rate: {target_to_comparison_rate:.2f}"  # noqa: E501
    )

    check_rate_and_notify(target_to_comparison_rate, threshold_rate)


if __name__ == "__main__":
    threshold_rate, target_currency, comparison_currency = prepare_inputs()
    exchange_rates = fetch_exchange_rates()
    # import os

    # dirname = os.path.dirname(__file__)
    # filename = os.path.join(dirname, "exchange_rates.json")
    # with open(filename, "r") as file:
    #     exchange_rates = json.load(file)
    print(f"Data timestamp: {date.fromtimestamp(exchange_rates['timestamp'])}")
    main(exchange_rates, threshold_rate, target_currency, comparison_currency)
