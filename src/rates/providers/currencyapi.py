"""currencyapi provider adapter."""

import os
import typing as t

from rates.http_client import request_json, safe_error_message
from rates.models import RateDetail


class CurrencyApiProvider:
    """Fetch base/quote rates from currencyapi latest endpoint."""

    source_name = "currencyapi"
    _api_url = "https://api.currencyapi.com/v3/latest"

    def __init__(
        self,
        api_key: t.Optional[str] = None,
        timeout_seconds: t.Optional[float] = None,
    ):
        self.api_key = api_key or os.environ.get("CURRENCYAPI_API_KEY", "").strip()
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _pair(base_currency: str, quote_currency: str) -> str:
        return f"{base_currency}/{quote_currency}"

    def fetch_rate(self, base_currency: str, quote_currency: str) -> RateDetail:
        """Fetch base/quote rate using currencyapi latest endpoint."""
        pair = self._pair(base_currency, quote_currency)

        try:
            if not self.api_key:
                raise ValueError(
                    "CURRENCYAPI_API_KEY is required for currencyapi provider"
                )

            payload = t.cast(
                t.Dict[str, t.Any],
                request_json(
                    self._api_url,
                    params={
                        "base_currency": base_currency,
                        "currencies": quote_currency,
                    },
                    headers={
                        "apikey": self.api_key,
                    },
                    timeout_seconds=self.timeout_seconds,
                ),
            )
            data = t.cast(t.Dict[str, t.Any], payload.get("data", {}))
            quote_data = t.cast(
                t.Optional[t.Dict[str, t.Any]], data.get(quote_currency)
            )

            if quote_data is None:
                raise ValueError(
                    f"Currency '{quote_currency}' not present in currencyapi response"
                )

            raw_value = quote_data.get("value")
            if raw_value is None:
                raise ValueError(
                    f"Missing value for currency '{quote_currency}' in currencyapi response"
                )

            return RateDetail(
                source=self.source_name,
                pair=pair,
                status="success",
                rate=float(raw_value),
                metadata={
                    "base_currency": base_currency,
                    "quote_currency": quote_currency,
                },
            )
        except Exception as error:  # pragma: no cover - exercised by tests via behavior
            return RateDetail(
                source=self.source_name,
                pair=pair,
                status="error",
                error=safe_error_message(error),
            )
