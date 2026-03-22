"""Tests for Bank Al-Maghrib provider adapter."""

from unittest.mock import patch

from rates.providers.bank_al_maghrib import BankAlMaghribProvider


class TestBankAlMaghribProvider:
    """Tests for BankAlMaghribProvider."""

    @patch("rates.providers.bank_al_maghrib.request_json")
    def test_returns_success_detail_with_achat_clientele(self, mock_request_json):
        """Provider should calculate cross rate from achatClientele quotes."""
        mock_request_json.return_value = [
            {
                "achatClientele": 10.1963,
                "date": "2026-03-18T08:30:00",
                "libDevise": "EUR",
                "uniteDevise": 1,
                "venteClientele": 11.8497,
            }
        ]

        provider = BankAlMaghribProvider(
            subscription_key="test_key", endpoint="CoursBBE"
        )
        detail = provider.fetch_rate("EUR", "MAD")

        assert detail.status == "success"
        assert detail.source == "bank_al_maghrib"
        assert detail.pair == "EUR/MAD"
        assert detail.rate == 10.1963
        assert detail.metadata["quote_field"] == "achatClientele"

    def test_returns_error_when_missing_subscription_key(self, monkeypatch):
        """Provider should return error detail when subscription key is missing."""
        monkeypatch.delenv("BAM_SUBSCRIPTION_KEY", raising=False)

        provider = BankAlMaghribProvider()
        detail = provider.fetch_rate("EUR", "MAD")

        assert detail.status == "error"
        assert "BAM_SUBSCRIPTION_KEY" in (detail.error or "")

    @patch("rates.providers.bank_al_maghrib.request_json")
    def test_returns_unavailable_when_no_quote(self, mock_request_json):
        """Provider should mark detail as unavailable when endpoint returns empty list."""
        mock_request_json.return_value = []

        provider = BankAlMaghribProvider(subscription_key="test_key")
        detail = provider.fetch_rate("EUR", "MAD")

        assert detail.status == "unavailable"
        assert "No quote returned" in (detail.error or "")
