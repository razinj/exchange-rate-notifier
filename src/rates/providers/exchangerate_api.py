"""ExchangeRate-API provider adapter."""

import os
import typing as t

from rates.http_client import request_json, safe_error_message
from rates.models import RateDetail


class ExchangeRateApiProvider:
    """Fetch pair conversion rates from ExchangeRate-API."""

    source_name = "exchangerate_api"
    _base_api_url = "https://v6.exchangerate-api.com/v6"

    def __init__(
        self,
        api_key: t.Optional[str] = None,
        timeout_seconds: t.Optional[float] = None,
    ):
        self.api_key = api_key or os.environ.get("EXCHANGERATE_API_KEY", "").strip()
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _pair(base_currency: str, quote_currency: str) -> str:
        return f"{base_currency}/{quote_currency}"

    def fetch_rate(self, base_currency: str, quote_currency: str) -> RateDetail:
        """Fetch base/quote rate using ExchangeRate-API pair endpoint."""
        pair = self._pair(base_currency, quote_currency)

        try:
            if not self.api_key:
                raise ValueError(
                    "EXCHANGERATE_API_KEY is required for exchangerate_api provider"
                )

            payload = t.cast(
                t.Dict[str, t.Any],
                request_json(
                    f"{self._base_api_url}/{self.api_key}/pair/{base_currency}/{quote_currency}",
                    timeout_seconds=self.timeout_seconds,
                ),
            )

            if payload.get("result") != "success":
                error_type = payload.get("error-type", "unknown-error")
                raise ValueError(f"ExchangeRate-API returned error: {error_type}")

            conversion_rate = payload.get("conversion_rate")
            if conversion_rate is None:
                raise ValueError(
                    "Missing 'conversion_rate' in ExchangeRate-API response"
                )

            return RateDetail(
                source=self.source_name,
                pair=pair,
                status="success",
                rate=float(conversion_rate),
                metadata={
                    "base_code": payload.get("base_code"),
                    "target_code": payload.get("target_code"),
                    "time_last_update_unix": payload.get("time_last_update_unix"),
                    "time_next_update_unix": payload.get("time_next_update_unix"),
                },
            )
        except Exception as error:  # pragma: no cover - exercised by tests via behavior
            return RateDetail(
                source=self.source_name,
                pair=pair,
                status="error",
                error=safe_error_message(error),
            )
