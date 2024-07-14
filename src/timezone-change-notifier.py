import datetime
import os

import pytz
from dotenv import load_dotenv

from email_client import send_email_mg  # type: ignore

load_dotenv()


def get_timezone_offset(tz: str) -> datetime.timedelta | None:
    timezone = pytz.timezone(tz)
    now = datetime.datetime.now(timezone)
    return now.utcoffset()


def main():
    TIMEZONE = os.getenv("TIMEZONE")
    INITIAL_TZ_OFFSET = os.getenv("INITIAL_TZ_OFFSET")

    if not TIMEZONE or not INITIAL_TZ_OFFSET:
        raise ValueError("City and initial timezone offset are required")

    current_timezone_offset = get_timezone_offset(TIMEZONE)
    if str(INITIAL_TZ_OFFSET) != str(current_timezone_offset):
        content = (
            "Update the cron to work with the current timezone and update the initial offset value to detect future changes."  # noqa: E501
            "\n"
            f"Current {TIMEZONE} timezone offset is {current_timezone_offset}"
        )
        print(content)
        send_email_mg(
            subject="[Exchange Rate Script] Timezone Change Detected", content=content
        )
    else:
        print(f"No change in timezone for {TIMEZONE} (offset {INITIAL_TZ_OFFSET}).")


if __name__ == "__main__":
    main()
