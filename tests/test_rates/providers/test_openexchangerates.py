"""Tests for OpenExchangeRates provider adapter."""

from unittest.mock import patch

from rates.providers.openexchangerates import OpenExchangeRatesProvider


class TestOpenExchangeRatesProvider:
    """Tests for OpenExchangeRatesProvider."""

    @patch("rates.providers.openexchangerates.request_json")
    def test_returns_success_detail(self, mock_request_json):
        """Provider should return a successful normalized detail."""
        mock_request_json.return_value = {
            "base": "USD",
            "timestamp": 1710750600,
            "rates": {
                "USD": 1.0,
                "EUR": 0.92,
                "MAD": 10.8,
            },
        }

        provider = OpenExchangeRatesProvider(app_id="test_app_id")
        detail = provider.fetch_rate("EUR", "MAD")

        assert detail.status == "success"
        assert detail.source == "openexchangerates"
        assert detail.pair == "EUR/MAD"
        assert detail.rate == 10.8 / 0.92
        assert detail.error is None

        mock_request_json.assert_called_once()

    def test_returns_error_when_missing_app_id(self, monkeypatch):
        """Provider should return error detail when APP ID is missing."""
        monkeypatch.delenv("OER_APP_ID", raising=False)

        provider = OpenExchangeRatesProvider()
        detail = provider.fetch_rate("EUR", "USD")

        assert detail.status == "error"
        assert "OER_APP_ID" in (detail.error or "")
