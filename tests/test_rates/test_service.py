"""Tests for rates service orchestration."""

import pytest

from rates.models import RateDetail
from rates.service import (
    aggregate_rate_details,
    get_enabled_provider_names,
    validate_min_successful_sources,
)


class TestGetEnabledProviderNames:
    """Tests for provider name parsing and validation."""

    def test_parses_provider_names(self, monkeypatch):
        """Comma-separated names should parse and normalize correctly."""
        monkeypatch.setenv(
            "RATE_SOURCES",
            "openexchangerates, exchangerate_api, currencyapi, "
            "apilayer_exchangeratesapi, fawazahmed0_exchange_api, bank_al_maghrib",
        )

        provider_names = get_enabled_provider_names()

        assert provider_names == [
            "openexchangerates",
            "exchangerate_api",
            "currencyapi",
            "apilayer_exchangeratesapi",
            "fawazahmed0_exchange_api",
            "bank_al_maghrib",
        ]

    def test_raises_for_unknown_provider(self, monkeypatch):
        """Unknown providers should fail validation."""
        monkeypatch.setenv("RATE_SOURCES", "openexchangerates,unknown")

        with pytest.raises(ValueError, match="Unknown provider"):
            get_enabled_provider_names()

    def test_deduplicates_provider_names_while_preserving_order(self, monkeypatch):
        """Duplicate provider entries should be removed while keeping order."""
        monkeypatch.setenv(
            "RATE_SOURCES",
            "openexchangerates,currencyapi,openexchangerates,currencyapi",
        )

        provider_names = get_enabled_provider_names()

        assert provider_names == ["openexchangerates", "currencyapi"]


class TestValidateMinSuccessfulSources:
    """Tests for min successful source count validation."""

    def test_raises_when_min_successful_exceeds_enabled_sources(self):
        """Validation should fail when required successful sources are unreachable."""
        with pytest.raises(
            ValueError, match="cannot be greater than number of enabled"
        ):
            validate_min_successful_sources(3, ["openexchangerates", "currencyapi"])


class TestAggregateRateDetails:
    """Tests for details-to-aggregate conversion."""

    def test_ignores_failed_sources(self):
        """Aggregation should only use successful source rates."""
        details = [
            RateDetail(source="a", pair="EUR/MAD", status="success", rate=0.1000),
            RateDetail(source="b", pair="EUR/MAD", status="error", error="timeout"),
            RateDetail(source="c", pair="EUR/MAD", status="success", rate=0.1020),
        ]

        result = aggregate_rate_details(
            base_currency="EUR",
            quote_currency="MAD",
            details=details,
            aggregation_method="median",
            min_successful_sources=1,
        )

        assert result.aggregated_rate == 0.1010
        assert result.successful_sources == 2
        assert result.failed_sources == 1

    def test_raises_when_not_enough_successful_sources(self):
        """Aggregation should fail when success count is below minimum."""
        details = [
            RateDetail(source="a", pair="EUR/MAD", status="error", error="timeout"),
            RateDetail(
                source="b", pair="EUR/MAD", status="unavailable", error="no quote"
            ),
        ]

        with pytest.raises(ValueError, match="Not enough successful sources"):
            aggregate_rate_details(
                base_currency="EUR",
                quote_currency="MAD",
                details=details,
                aggregation_method="median",
                min_successful_sources=1,
            )
