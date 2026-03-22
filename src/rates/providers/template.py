"""Template provider for quickly adding a new exchange-rate source.

Copy this file, rename the class, and adapt the request + parsing logic.
"""

import os
import typing as t

from rates.http_client import request_json, safe_error_message
from rates.models import RateDetail


class TemplateProvider:
    """Reference implementation skeleton for a new provider adapter."""

    source_name = "template_provider"
    _api_url = "https://example.com/latest"

    def __init__(
        self,
        api_key: t.Optional[str] = None,
        timeout_seconds: t.Optional[float] = None,
    ):
        self.api_key = api_key or os.environ.get("TEMPLATE_API_KEY", "").strip()
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _pair(base_currency: str, quote_currency: str) -> str:
        return f"{base_currency}/{quote_currency}"

    def fetch_rate(self, base_currency: str, quote_currency: str) -> RateDetail:
        """Return a normalized result for base/quote using this source."""
        pair = self._pair(base_currency, quote_currency)

        try:
            # Replace this request and response mapping with your API logic.
            payload = t.cast(
                t.Dict[str, t.Any],
                request_json(
                    self._api_url,
                    params={
                        "base": base_currency,
                        "symbols": quote_currency,
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                    },
                    timeout_seconds=self.timeout_seconds,
                ),
            )

            # Normalize source fields to a single float for base/quote.
            # Example when API already returns base/quote directly:
            # rate = float(payload["data"]["rate"])
            #
            # Example when API uses base->currency map:
            # provider_base_to_quote = float(payload["rates"][quote_currency])
            # rate = provider_base_to_quote
            rate = float(payload["rate"])

            return RateDetail(
                source=self.source_name,
                pair=pair,
                status="success",
                rate=rate,
                metadata={"raw": payload},
            )
        except Exception as error:
            return RateDetail(
                source=self.source_name,
                pair=pair,
                status="error",
                error=safe_error_message(error),
            )
