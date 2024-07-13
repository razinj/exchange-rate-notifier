import os
import typing as t

import httpx
from dotenv import load_dotenv

load_dotenv()

MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_FROM = os.getenv("MAILGUN_FROM")
MAILGUN_TO = os.getenv("MAILGUN_TO")


def send_email_mg(subject: str, content: str) -> None:
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
