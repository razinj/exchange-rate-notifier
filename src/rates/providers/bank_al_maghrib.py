"""Bank Al-Maghrib provider adapter."""

import os
import typing as t

from rates.http_client import request_json, safe_error_message
from rates.models import RateDetail


class QuoteUnavailableError(Exception):
    """Raised when the provider returns no quote for the requested currency."""


class BankAlMaghribProvider:
    """Fetch cross rates from Bank Al-Maghrib using achatClientele quotes."""

    source_name = "bank_al_maghrib"
    _base_api_url = "https://api.centralbankofmorocco.ma/cours/Version1/api"

    def __init__(
        self,
        subscription_key: t.Optional[str] = None,
        endpoint: t.Optional[str] = None,
        timeout_seconds: t.Optional[float] = None,
    ):
        self.subscription_key = (
            subscription_key or os.environ.get("BAM_SUBSCRIPTION_KEY", "").strip()
        )
        self.endpoint = endpoint or os.environ.get("BAM_ENDPOINT", "CoursBBE").strip()
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _pair(base_currency: str, quote_currency: str) -> str:
        return f"{base_currency}/{quote_currency}"

    def _fetch_quote(self, currency: str) -> t.Dict[str, t.Any]:
        if not self.subscription_key:
            raise ValueError(
                "BAM_SUBSCRIPTION_KEY is required for bank_al_maghrib provider"
            )

        payload = t.cast(
            t.List[t.Dict[str, t.Any]],
            request_json(
                f"{self._base_api_url}/{self.endpoint}",
                params={"libDevise": currency},
                headers={
                    "Cache-Control": "no-cache",
                    "Ocp-Apim-Subscription-Key": self.subscription_key,
                },
                timeout_seconds=self.timeout_seconds,
            ),
        )
        if not payload:
            raise QuoteUnavailableError(
                f"No quote returned by BAM for currency '{currency}'"
            )

        return payload[0]

    def _mad_per_currency(
        self, currency: str
    ) -> t.Tuple[float, t.Optional[t.Dict[str, t.Any]]]:
        if currency == "MAD":
            return 1.0, None

        quote = self._fetch_quote(currency)

        achat_clientele = float(quote["achatClientele"])
        unite_devise = float(quote.get("uniteDevise") or 1)

        if unite_devise <= 0:
            raise ValueError(
                f"Invalid uniteDevise value '{unite_devise}' for currency '{currency}'"
            )

        mad_per_currency = achat_clientele / unite_devise
        return mad_per_currency, quote

    def fetch_rate(self, base_currency: str, quote_currency: str) -> RateDetail:
        """Fetch base/quote cross rate using MAD-based achatClientele quotes."""
        pair = self._pair(base_currency, quote_currency)

        try:
            mad_per_base, base_currency_quote = self._mad_per_currency(base_currency)
            mad_per_quote, quote_currency_quote = self._mad_per_currency(quote_currency)
            cross_rate = mad_per_base / mad_per_quote

            return RateDetail(
                source=self.source_name,
                pair=pair,
                status="success",
                rate=cross_rate,
                metadata={
                    "endpoint": self.endpoint,
                    "quote_field": "achatClientele",
                    "base_currency_quote": base_currency_quote,
                    "quote_currency_quote": quote_currency_quote,
                },
            )
        except QuoteUnavailableError as error:
            return RateDetail(
                source=self.source_name,
                pair=pair,
                status="unavailable",
                error=safe_error_message(error),
                metadata={
                    "endpoint": self.endpoint,
                    "quote_field": "achatClientele",
                },
            )
        except Exception as error:  # pragma: no cover - exercised by tests via behavior
            return RateDetail(
                source=self.source_name,
                pair=pair,
                status="error",
                error=safe_error_message(error),
                metadata={
                    "endpoint": self.endpoint,
                    "quote_field": "achatClientele",
                },
            )
