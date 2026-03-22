"""Tests for apilayer exchangeratesapi provider adapter."""

from unittest.mock import patch

from rates.providers.apilayer_exchangeratesapi import ApilayerExchangeRatesApiProvider


class TestApilayerExchangeRatesApiProvider:
    """Tests for ApilayerExchangeRatesApiProvider."""

    @patch("rates.providers.apilayer_exchangeratesapi.request_json")
    def test_returns_success_detail(self, mock_request_json):
        """Provider should return a successful normalized detail."""
        mock_request_json.return_value = {
            "success": True,
            "timestamp": 1719408000,
            "base": "EUR",
            "date": "2024-06-26",
            "rates": {
                "MAD": 10.7511,
            },
        }

        provider = ApilayerExchangeRatesApiProvider(access_key="test_access_key")
        detail = provider.fetch_rate("EUR", "MAD")

        assert detail.status == "success"
        assert detail.source == "apilayer_exchangeratesapi"
        assert detail.pair == "EUR/MAD"
        assert detail.rate == 10.7511
        assert detail.error is None

        mock_request_json.assert_called_once_with(
            "https://api.exchangeratesapi.io/v1/latest",
            params={
                "access_key": "test_access_key",
                "symbols": "EUR,MAD",
            },
            timeout_seconds=None,
        )

    def test_returns_error_when_missing_key(self, monkeypatch):
        """Provider should return error detail when access key is missing."""
        monkeypatch.delenv("APILAYER_EXCHANGERATESAPI_ACCESS_KEY", raising=False)

        provider = ApilayerExchangeRatesApiProvider()
        detail = provider.fetch_rate("EUR", "MAD")

        assert detail.status == "error"
        assert "APILAYER_EXCHANGERATESAPI_ACCESS_KEY" in (detail.error or "")

    @patch("rates.providers.apilayer_exchangeratesapi.request_json")
    def test_returns_error_when_api_reports_failure(self, mock_request_json):
        """Provider should return error detail when API success flag is false."""
        mock_request_json.return_value = {
            "success": False,
            "error": {
                "code": 101,
                "type": "invalid_access_key",
                "info": "You have not supplied a valid API Access Key.",
            },
        }

        provider = ApilayerExchangeRatesApiProvider(access_key="bad_key")
        detail = provider.fetch_rate("EUR", "MAD")

        assert detail.status == "error"
        assert "invalid_access_key" in (detail.error or "")

    @patch("rates.providers.apilayer_exchangeratesapi.request_json")
    def test_returns_error_when_requested_currency_missing_in_rates(
        self, mock_request_json
    ):
        """Provider should return error detail when response misses requested rate."""
        mock_request_json.return_value = {
            "success": True,
            "timestamp": 1719408000,
            "base": "EUR",
            "date": "2024-06-26",
            "rates": {
                "USD": 1.0712,
            },
        }

        provider = ApilayerExchangeRatesApiProvider(access_key="test_access_key")
        detail = provider.fetch_rate("USD", "MAD")

        assert detail.status == "error"
        assert "Currency 'MAD'" in (detail.error or "")
