"""OpenExchangeRates provider adapter."""

import os
import typing as t

from rates.http_client import request_json, safe_error_message
from rates.models import RateDetail


class OpenExchangeRatesProvider:
    """Fetch cross rates from OpenExchangeRates latest endpoint."""

    source_name = "openexchangerates"
    _api_url = "https://openexchangerates.org/api/latest.json"

    def __init__(
        self,
        app_id: t.Optional[str] = None,
        timeout_seconds: t.Optional[float] = None,
    ):
        self.app_id = app_id or os.environ.get("OER_APP_ID", "").strip()
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _pair(base_currency: str, quote_currency: str) -> str:
        return f"{base_currency}/{quote_currency}"

    @staticmethod
    def _usd_to_currency(rates: t.Dict[str, t.Any], currency: str) -> float:
        if currency == "USD":
            return 1.0

        value = rates.get(currency)
        if value is None:
            raise ValueError(
                f"Currency '{currency}' is not available in OpenExchangeRates response"
            )

        return float(value)

    def fetch_rate(self, base_currency: str, quote_currency: str) -> RateDetail:
        """Fetch base/quote cross rate using USD base rates."""
        pair = self._pair(base_currency, quote_currency)

        try:
            if not self.app_id:
                raise ValueError(
                    "OER_APP_ID is required for openexchangerates provider"
                )

            payload = t.cast(
                t.Dict[str, t.Any],
                request_json(
                    self._api_url,
                    params={"app_id": self.app_id},
                    timeout_seconds=self.timeout_seconds,
                ),
            )
            rates = t.cast(t.Dict[str, t.Any], payload.get("rates", {}))

            usd_to_base = self._usd_to_currency(rates, base_currency)
            usd_to_quote = self._usd_to_currency(rates, quote_currency)
            cross_rate = usd_to_quote / usd_to_base

            return RateDetail(
                source=self.source_name,
                pair=pair,
                status="success",
                rate=cross_rate,
                metadata={
                    "base": payload.get("base"),
                    "timestamp": payload.get("timestamp"),
                },
            )
        except Exception as error:  # pragma: no cover - exercised by tests via behavior
            return RateDetail(
                source=self.source_name,
                pair=pair,
                status="error",
                error=safe_error_message(error),
            )
