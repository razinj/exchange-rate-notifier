"""Tests for fawazahmed0 exchange-api provider adapter."""

from unittest.mock import patch

from rates.providers.fawazahmed0_exchange_api import FawazAhmed0ExchangeApiProvider


class TestFawazAhmed0ExchangeApiProvider:
    """Tests for FawazAhmed0ExchangeApiProvider."""

    @patch("rates.providers.fawazahmed0_exchange_api.request_json")
    def test_returns_success_detail(self, mock_request_json):
        """Provider should return a successful normalized detail."""
        mock_request_json.return_value = {
            "date": "2026-03-21",
            "eur": {
                "mad": 10.7511,
            },
        }

        provider = FawazAhmed0ExchangeApiProvider(date_tag="latest")
        detail = provider.fetch_rate("EUR", "MAD")

        assert detail.status == "success"
        assert detail.source == "fawazahmed0_exchange_api"
        assert detail.pair == "EUR/MAD"
        assert detail.rate == 10.7511
        assert detail.error is None
        assert detail.metadata["resolved_url"].startswith(
            "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/"
        )

    @patch("rates.providers.fawazahmed0_exchange_api.request_json")
    def test_uses_fallback_when_primary_fails(self, mock_request_json):
        """Provider should use fallback URL when primary endpoint fails."""
        fallback_response = {
            "date": "2026-03-21",
            "eur": {
                "mad": 10.7511,
            },
        }

        mock_request_json.side_effect = [
            RuntimeError("primary down"),
            fallback_response,
        ]

        provider = FawazAhmed0ExchangeApiProvider(date_tag="latest")
        detail = provider.fetch_rate("EUR", "MAD")

        assert detail.status == "success"
        assert detail.metadata["resolved_url"] == (
            "https://latest.currency-api.pages.dev/v1/currencies/eur.json"
        )
        assert mock_request_json.call_count == 2

    @patch("rates.providers.fawazahmed0_exchange_api.request_json")
    def test_returns_error_when_quote_currency_missing(self, mock_request_json):
        """Provider should return error detail when quote currency is absent."""
        mock_request_json.return_value = {
            "date": "2026-03-21",
            "eur": {
                "usd": 1.08,
            },
        }

        provider = FawazAhmed0ExchangeApiProvider(date_tag="latest")
        detail = provider.fetch_rate("EUR", "MAD")

        assert detail.status == "error"
        assert "Currency 'MAD'" in (detail.error or "")

    def test_returns_error_when_date_tag_is_empty(self):
        """Provider should return error detail when date tag is empty."""
        provider = FawazAhmed0ExchangeApiProvider(date_tag="")
        detail = provider.fetch_rate("EUR", "MAD")

        assert detail.status == "error"
        assert "FAWAZAHMED0_CURRENCY_API_DATE" in (detail.error or "")
