"""apilayer exchangeratesapi provider adapter."""

import os
import typing as t

from rates.http_client import request_json, safe_error_message
from rates.models import RateDetail


class ApilayerExchangeRatesApiProvider:
    """Fetch cross rates from apilayer exchangeratesapi latest endpoint."""

    source_name = "apilayer_exchangeratesapi"
    _api_url = "https://api.exchangeratesapi.io/v1/latest"

    def __init__(
        self,
        access_key: t.Optional[str] = None,
        timeout_seconds: t.Optional[float] = None,
    ):
        self.access_key = (
            access_key
            or os.environ.get("APILAYER_EXCHANGERATESAPI_ACCESS_KEY", "").strip()
        )
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _pair(base_currency: str, quote_currency: str) -> str:
        return f"{base_currency}/{quote_currency}"

    @staticmethod
    def _base_to_currency(rates: t.Dict[str, t.Any], base: str, currency: str) -> float:
        if currency == base:
            return 1.0

        value = rates.get(currency)
        if value is None:
            raise ValueError(
                f"Currency '{currency}' is not available in apilayer exchangeratesapi response"
            )

        return float(value)

    @staticmethod
    def _raise_api_error(payload: t.Dict[str, t.Any]) -> None:
        error = payload.get("error")
        if not isinstance(error, dict):
            raise ValueError("apilayer exchangeratesapi returned an unknown API error")

        code = error.get("code", "unknown")
        error_type = error.get("type", "unknown")
        info = error.get("info", "No details provided")

        raise ValueError(
            f"apilayer exchangeratesapi error ({code}/{error_type}): {info}"
        )

    def fetch_rate(self, base_currency: str, quote_currency: str) -> RateDetail:
        """Fetch base/quote cross rate via latest endpoint."""
        pair = self._pair(base_currency, quote_currency)

        try:
            if not self.access_key:
                raise ValueError(
                    "APILAYER_EXCHANGERATESAPI_ACCESS_KEY is required for apilayer_exchangeratesapi provider"
                )

            payload = t.cast(
                t.Dict[str, t.Any],
                request_json(
                    self._api_url,
                    params={
                        "access_key": self.access_key,
                        "symbols": f"{base_currency},{quote_currency}",
                    },
                    timeout_seconds=self.timeout_seconds,
                ),
            )

            if payload.get("success") is False:
                self._raise_api_error(payload)

            rates = t.cast(t.Dict[str, t.Any], payload.get("rates", {}))
            provider_base_currency = str(payload.get("base") or "")
            if not provider_base_currency:
                raise ValueError("Missing 'base' in apilayer exchangeratesapi response")

            provider_base_to_base = self._base_to_currency(
                rates,
                provider_base_currency,
                base_currency,
            )
            provider_base_to_quote = self._base_to_currency(
                rates,
                provider_base_currency,
                quote_currency,
            )
            cross_rate = provider_base_to_quote / provider_base_to_base

            return RateDetail(
                source=self.source_name,
                pair=pair,
                status="success",
                rate=cross_rate,
                metadata={
                    "provider_base": provider_base_currency,
                    "date": payload.get("date"),
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
