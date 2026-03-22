"""Provider protocol for normalized exchange rate adapters."""

import typing as t

from rates.models import RateDetail


class ExchangeRateProvider(t.Protocol):
    """Protocol implemented by all exchange rate providers."""

    source_name: str

    def fetch_rate(self, base_currency: str, quote_currency: str) -> RateDetail:
        """Fetch base/quote rate and return normalized source details."""
        ...
