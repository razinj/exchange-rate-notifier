"""Shared HTTP helpers for provider calls with retry support."""

import os
import random
import re
import time
import typing as t

import httpx

TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}


def get_http_timeout_seconds() -> float:
    """Read and validate HTTP timeout in seconds."""
    raw_value = os.environ.get("HTTP_TIMEOUT_SECONDS", "12").strip()
    timeout_seconds = float(raw_value)

    if timeout_seconds <= 0:
        raise ValueError("HTTP_TIMEOUT_SECONDS must be greater than 0")

    return timeout_seconds


def get_http_max_retries() -> int:
    """Read and validate max retry attempts for transient failures."""
    raw_value = os.environ.get("HTTP_MAX_RETRIES", "2").strip()
    max_retries = int(raw_value)

    if max_retries < 0:
        raise ValueError("HTTP_MAX_RETRIES cannot be negative")

    return max_retries


def get_http_backoff_base_seconds() -> float:
    """Read and validate exponential backoff base delay."""
    raw_value = os.environ.get("HTTP_BACKOFF_BASE_SECONDS", "0.5").strip()
    backoff_base_seconds = float(raw_value)

    if backoff_base_seconds < 0:
        raise ValueError("HTTP_BACKOFF_BASE_SECONDS cannot be negative")

    return backoff_base_seconds


def get_http_backoff_max_seconds() -> float:
    """Read and validate maximum backoff delay."""
    raw_value = os.environ.get("HTTP_BACKOFF_MAX_SECONDS", "4").strip()
    backoff_max_seconds = float(raw_value)

    if backoff_max_seconds < 0:
        raise ValueError("HTTP_BACKOFF_MAX_SECONDS cannot be negative")

    return backoff_max_seconds


def sanitize_error_message(message: str) -> str:
    """Redact sensitive tokens and keys from raw error messages."""
    sanitized = message

    sanitized = re.sub(
        r"([?&](?:app_id|access_key|api_key|apikey|subscription_key|token)=)[^&\s]+",
        r"\1<redacted>",
        sanitized,
        flags=re.IGNORECASE,
    )

    sanitized = re.sub(
        r"(/v6/)[^/]+(/pair/)",
        r"\1<redacted>\2",
        sanitized,
        flags=re.IGNORECASE,
    )

    sanitized = re.sub(
        r"(Ocp-Apim-Subscription-Key['\"]?\s*[:=]\s*['\"]?)[^'\",\s]+",
        r"\1<redacted>",
        sanitized,
        flags=re.IGNORECASE,
    )

    return sanitized


def safe_error_message(error: Exception) -> str:
    """Return a sanitized string representation of an error."""
    return sanitize_error_message(str(error))


def _is_transient_error(error: Exception) -> bool:
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code in TRANSIENT_STATUS_CODES

    if isinstance(error, httpx.RequestError):
        return True

    return False


def _get_retry_after_seconds(error: Exception) -> t.Optional[float]:
    if not isinstance(error, httpx.HTTPStatusError):
        return None

    retry_after = error.response.headers.get("Retry-After")
    if retry_after is None:
        return None

    try:
        retry_after_seconds = float(retry_after)
    except ValueError:
        return None

    return max(0.0, retry_after_seconds)


def _compute_backoff_delay_seconds(attempt_index: int) -> float:
    base_delay_seconds = get_http_backoff_base_seconds()
    max_delay_seconds = get_http_backoff_max_seconds()

    if max_delay_seconds == 0 or base_delay_seconds == 0:
        return 0.0

    exponential_delay = base_delay_seconds * (2**attempt_index)
    jitter = random.uniform(0.0, base_delay_seconds)

    return float(min(max_delay_seconds, exponential_delay + jitter))


def request_json(
    url: str,
    params: t.Optional[t.Mapping[str, t.Any]] = None,
    headers: t.Optional[t.Mapping[str, str]] = None,
    timeout_seconds: t.Optional[float] = None,
) -> t.Any:
    """Perform an HTTP GET request and parse JSON with retry on transient errors."""
    timeout = (
        timeout_seconds if timeout_seconds is not None else get_http_timeout_seconds()
    )
    max_retries = get_http_max_retries()

    for attempt in range(max_retries + 1):
        try:
            response = httpx.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as error:
            should_retry = attempt < max_retries and _is_transient_error(error)
            if not should_retry:
                raise

            retry_after_seconds = _get_retry_after_seconds(error)
            delay_seconds = (
                retry_after_seconds
                if retry_after_seconds is not None
                else _compute_backoff_delay_seconds(attempt)
            )

            if delay_seconds > 0:
                time.sleep(delay_seconds)

    raise RuntimeError(f"Unexpected retry flow ended for URL: {url}")
