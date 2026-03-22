"""Tests for ExchangeRate-API provider adapter."""

from unittest.mock import patch

from rates.providers.exchangerate_api import ExchangeRateApiProvider


class TestExchangeRateApiProvider:
    """Tests for ExchangeRateApiProvider."""

    @patch("rates.providers.exchangerate_api.request_json")
    def test_returns_success_detail(self, mock_request_json):
        """Provider should return a successful normalized detail."""
        mock_request_json.return_value = {
            "result": "success",
            "time_last_update_unix": 1585267200,
            "time_last_update_utc": "Fri, 27 Mar 2020 00:00:00 +0000",
            "time_next_update_unix": 1585270800,
            "base_code": "EUR",
            "target_code": "MAD",
            "conversion_rate": 10.7296,
        }

        provider = ExchangeRateApiProvider(api_key="test_key")
        detail = provider.fetch_rate("EUR", "MAD")

        assert detail.status == "success"
        assert detail.source == "exchangerate_api"
        assert detail.pair == "EUR/MAD"
        assert detail.rate == 10.7296
        assert detail.error is None
        assert detail.metadata["base_code"] == "EUR"
        assert detail.metadata["target_code"] == "MAD"

        mock_request_json.assert_called_once_with(
            "https://v6.exchangerate-api.com/v6/test_key/pair/EUR/MAD",
            timeout_seconds=None,
        )

    @patch("rates.providers.exchangerate_api.request_json")
    def test_supports_explicit_timeout_override(self, mock_request_json):
        """Explicit timeout should override global HTTP timeout fallback."""
        mock_request_json.return_value = {
            "result": "success",
            "conversion_rate": 10.7296,
        }

        provider = ExchangeRateApiProvider(api_key="test_key", timeout_seconds=7.5)
        detail = provider.fetch_rate("EUR", "MAD")

        assert detail.status == "success"
        mock_request_json.assert_called_once_with(
            "https://v6.exchangerate-api.com/v6/test_key/pair/EUR/MAD",
            timeout_seconds=7.5,
        )

    def test_returns_error_when_missing_key(self, monkeypatch):
        """Provider should return error detail when API key is missing."""
        monkeypatch.delenv("EXCHANGERATE_API_KEY", raising=False)

        provider = ExchangeRateApiProvider()
        detail = provider.fetch_rate("EUR", "MAD")

        assert detail.status == "error"
        assert "EXCHANGERATE_API_KEY" in (detail.error or "")

    @patch("rates.providers.exchangerate_api.request_json")
    def test_returns_error_when_api_returns_error_payload(self, mock_request_json):
        """Provider should return error detail when API payload result is error."""
        mock_request_json.return_value = {
            "result": "error",
            "error-type": "quota-reached",
        }

        provider = ExchangeRateApiProvider(api_key="test_key")
        detail = provider.fetch_rate("EUR", "MAD")

        assert detail.status == "error"
        assert "quota-reached" in (detail.error or "")
