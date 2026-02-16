"""Notification module using apprise for flexible multi-medium notifications."""

import os
import typing as t

import apprise


def _build_mailgun_url() -> t.Optional[str]:
    """Build apprise Mailgun URL from environment variables."""
    domain = os.environ.get("MAILGUN_DOMAIN", "").strip()
    api_key = os.environ.get("MAILGUN_API_KEY", "").strip()
    from_addr = os.environ.get("MAILGUN_FROM", "").strip()
    to_addrs = os.environ.get("MAILGUN_TO", "").strip()

    if not all([domain, api_key, from_addr, to_addrs]):
        return None

    # Split multiple emails by comma and join with /
    to_list = "/".join(email.strip() for email in to_addrs.split(","))

    # Build URL: mailgun://user@domain/apikey/to1/to2/?region=eu
    return f"mailgun://no-reply@{domain}/{api_key}/{to_list}/?region=eu&name=Exchange Rate Script"


def _build_gotify_url() -> t.Optional[str]:
    """Build apprise Gotify URL from environment variables."""
    url = os.environ.get("GOTIFY_URL", "").strip()
    token = os.environ.get("GOTIFY_TOKEN", "").strip()

    if not url or not token:
        return None

    # Handle HTTPS vs HTTP
    if url.startswith("https://"):
        hostname = url.replace("https://", "")
        return f"gotifys://{hostname}/{token}"
    elif url.startswith("http://"):
        hostname = url.replace("http://", "")
        return f"gotify://{hostname}/{token}"
    else:
        # Assume HTTPS if no protocol specified
        return f"gotifys://{url}/{token}"


def get_notification_manager() -> apprise.Apprise:
    """Build and return an Apprise notification manager with all configured targets."""
    apobj = apprise.Apprise()

    # Mailgun (email)
    mailgun_url = _build_mailgun_url()
    if mailgun_url:
        apobj.add(mailgun_url)
        print("[Notifications] Mailgun configured")

    # Gotify
    gotify_url = _build_gotify_url()
    if gotify_url:
        apobj.add(gotify_url)
        print("[Notifications] Gotify configured")

    return apobj


def notify(subject: str, body: str) -> bool:
    """
    Send notification to all configured mediums.

    Args:
        subject: The notification title/subject
        body: The notification message body

    Returns:
        True if at least one notification was sent successfully
    """
    apobj = get_notification_manager()

    if not apobj:
        print("[Notifications] Warning: No notification targets configured")
        return False

    result = apobj.notify(body=body, title=subject)

    success = bool(result)

    if success:
        print("[Notifications] Notification sent successfully")
    else:
        print("[Notifications] Failed to send notification")

    return success
