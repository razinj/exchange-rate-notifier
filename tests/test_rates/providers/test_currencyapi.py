"""Tests for currencyapi provider adapter."""

from unittest.mock import patch

from rates.providers.currencyapi import CurrencyApiProvider


class TestCurrencyApiProvider:
    """Tests for CurrencyApiProvider."""

    @patch("rates.providers.currencyapi.request_json")
    def test_returns_success_detail(self, mock_request_json):
        """Provider should return a successful normalized detail."""
        mock_request_json.return_value = {
            "meta": {
                "last_updated_at": "2023-06-23T10:15:59Z",
            },
            "data": {
                "MAD": {
                    "code": "MAD",
                    "value": 10.7311,
                }
            },
        }

        provider = CurrencyApiProvider(api_key="test_currencyapi_key")
        detail = provider.fetch_rate("EUR", "MAD")

        assert detail.status == "success"
        assert detail.source == "currencyapi"
        assert detail.pair == "EUR/MAD"
        assert detail.rate == 10.7311
        assert detail.error is None

        mock_request_json.assert_called_once_with(
            "https://api.currencyapi.com/v3/latest",
            params={"base_currency": "EUR", "currencies": "MAD"},
            headers={"apikey": "test_currencyapi_key"},
            timeout_seconds=None,
        )

    def test_returns_error_when_missing_key(self, monkeypatch):
        """Provider should return error detail when API key is missing."""
        monkeypatch.delenv("CURRENCYAPI_API_KEY", raising=False)

        provider = CurrencyApiProvider()
        detail = provider.fetch_rate("EUR", "MAD")

        assert detail.status == "error"
        assert "CURRENCYAPI_API_KEY" in (detail.error or "")

    @patch("rates.providers.currencyapi.request_json")
    def test_returns_error_when_quote_currency_is_missing(self, mock_request_json):
        """Provider should return error detail when quote currency is absent."""
        mock_request_json.return_value = {
            "meta": {
                "last_updated_at": "2023-06-23T10:15:59Z",
            },
            "data": {
                "USD": {
                    "code": "USD",
                    "value": 1.0,
                }
            },
        }

        provider = CurrencyApiProvider(api_key="test_currencyapi_key")
        detail = provider.fetch_rate("EUR", "MAD")

        assert detail.status == "error"
        assert "not present" in (detail.error or "")
