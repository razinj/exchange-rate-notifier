"""fawazahmed0 exchange-api provider adapter."""

import os
import typing as t

from rates.http_client import request_json, safe_error_message
from rates.models import RateDetail


class FawazAhmed0ExchangeApiProvider:
    """Fetch base/quote rates from fawazahmed0 exchange-api."""

    source_name = "fawazahmed0_exchange_api"
    _primary_url_template = (
        "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@"
        "{date}/v1/currencies/{base}.json"
    )
    _fallback_url_template = (
        "https://{date}.currency-api.pages.dev/v1/currencies/{base}.json"
    )

    def __init__(
        self,
        date_tag: t.Optional[str] = None,
        timeout_seconds: t.Optional[float] = None,
    ):
        raw_date_tag = (
            date_tag
            if date_tag is not None
            else os.environ.get("FAWAZAHMED0_CURRENCY_API_DATE", "latest")
        )

        self.date_tag = raw_date_tag.strip()
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _pair(base_currency: str, quote_currency: str) -> str:
        return f"{base_currency}/{quote_currency}"

    def _build_urls(self, base_currency: str) -> t.List[str]:
        base = base_currency.lower()
        return [
            self._primary_url_template.format(
                date=self.date_tag,
                base=base,
            ),
            self._fallback_url_template.format(
                date=self.date_tag,
                base=base,
            ),
        ]

    def _fetch_payload(self, base_currency: str) -> t.Tuple[t.Dict[str, t.Any], str]:
        errors: t.List[str] = []

        for url in self._build_urls(base_currency):
            try:
                payload = t.cast(
                    t.Dict[str, t.Any],
                    request_json(url, timeout_seconds=self.timeout_seconds),
                )
                return payload, url
            except Exception as error:
                errors.append(f"{url}: {safe_error_message(error)}")

        raise ValueError(
            "Failed to fetch fawazahmed0 exchange-api payload from all endpoints: "
            + " | ".join(errors)
        )

    @staticmethod
    def _extract_rate(
        payload: t.Dict[str, t.Any],
        base_currency: str,
        quote_currency: str,
    ) -> float:
        base = base_currency.lower()
        quote = quote_currency.lower()

        rates = t.cast(t.Dict[str, t.Any], payload.get(base, {}))
        if not rates:
            raise ValueError(
                f"Currency '{base_currency}' block is missing in fawazahmed0 exchange-api response"
            )

        rate_value = rates.get(quote)
        if rate_value is None:
            raise ValueError(
                f"Currency '{quote_currency}' is missing in fawazahmed0 exchange-api response"
            )

        return float(rate_value)

    def fetch_rate(self, base_currency: str, quote_currency: str) -> RateDetail:
        """Fetch base/quote rate from fawazahmed0 exchange-api."""
        pair = self._pair(base_currency, quote_currency)

        try:
            if not self.date_tag:
                raise ValueError(
                    "FAWAZAHMED0_CURRENCY_API_DATE cannot be empty when fawazahmed0_exchange_api is enabled"
                )

            payload, resolved_url = self._fetch_payload(base_currency)
            rate = self._extract_rate(payload, base_currency, quote_currency)

            return RateDetail(
                source=self.source_name,
                pair=pair,
                status="success",
                rate=rate,
                metadata={
                    "resolved_url": resolved_url,
                    "date_tag": self.date_tag,
                },
            )
        except Exception as error:  # pragma: no cover - exercised by tests via behavior
            return RateDetail(
                source=self.source_name,
                pair=pair,
                status="error",
                error=safe_error_message(error),
            )
