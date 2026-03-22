"""Tests for the main script module."""

import pytest

from rates.models import AggregatedRateResult, RateDetail
from script import check_and_notify, prepare_inputs


class TestPrepareInputs:
    """Tests for prepare_inputs function."""

    def test_valid_inputs(self, mock_env_vars):
        """Test valid inputs are parsed correctly."""
        threshold, base, quote = prepare_inputs()

        assert threshold == 0.9
        assert base == "EUR"
        assert quote == "USD"

    def test_raises_when_currency_vars_are_missing(self, monkeypatch, mock_env_vars):
        """Missing base variable should raise ValueError."""
        monkeypatch.delenv("BASE_CURRENCY", raising=False)

        with pytest.raises(ValueError, match="BASE_CURRENCY is required"):
            prepare_inputs()

    def test_negative_threshold_raises_error(self, monkeypatch, mock_env_vars):
        """Test that negative threshold raises ValueError."""
        monkeypatch.setenv("THRESHOLD_RATE", "-1.0")

        with pytest.raises(ValueError, match="positive number"):
            prepare_inputs()


class TestCheckAndNotify:
    """Tests for check_and_notify function."""

    def test_notifies_when_threshold_met(self, mocker, mock_env_vars):
        """Test notification sent when aggregated rate >= threshold."""
        details = [
            RateDetail(
                source="openexchangerates",
                pair="EUR/USD",
                status="success",
                rate=0.95,
            ),
            RateDetail(
                source="bank_al_maghrib",
                pair="EUR/USD",
                status="success",
                rate=0.94,
            ),
        ]

        mocker.patch("script.get_aggregation_method", return_value="median")
        mocker.patch(
            "script.get_enabled_provider_names",
            return_value=["openexchangerates", "bank_al_maghrib"],
        )
        mocker.patch("script.get_min_successful_sources", return_value=1)
        mocker.patch("script.fetch_rate_details", return_value=details)

        mocker.patch(
            "script.aggregate_rate_details",
            return_value=AggregatedRateResult(
                pair="EUR/USD",
                aggregation_method="median",
                aggregated_rate=0.945,
                details=details,
                successful_sources=2,
                failed_sources=0,
            ),
        )
        mock_notify = mocker.patch("script.notify")

        check_and_notify()

        mock_notify.assert_called_once()
        call_args = mock_notify.call_args
        assert "EUR/USD" in call_args[0][0]
        assert "Source details" in call_args[0][1]
        assert "openexchangerates" in call_args[0][1]
        assert "bank_al_maghrib" in call_args[0][1]

    def test_no_notification_when_below_threshold(self, mocker, mock_env_vars):
        """Test no notification when aggregated rate is below threshold."""
        details = [
            RateDetail(
                source="openexchangerates",
                pair="EUR/USD",
                status="success",
                rate=0.80,
            )
        ]

        mocker.patch("script.get_aggregation_method", return_value="median")
        mocker.patch(
            "script.get_enabled_provider_names", return_value=["openexchangerates"]
        )
        mocker.patch("script.get_min_successful_sources", return_value=1)
        mocker.patch("script.fetch_rate_details", return_value=details)
        mocker.patch(
            "script.aggregate_rate_details",
            return_value=AggregatedRateResult(
                pair="EUR/USD",
                aggregation_method="median",
                aggregated_rate=0.80,
                details=details,
                successful_sources=1,
                failed_sources=0,
            ),
        )

        mock_notify = mocker.patch("script.notify")
        mock_print = mocker.patch("builtins.print")

        check_and_notify()

        mock_notify.assert_not_called()
        mock_print.assert_any_call(
            "The current EUR/USD exchange rate is 0.8000, which is below the threshold rate 0.9000."
        )

    def test_notifies_when_aggregation_fails_and_config_enabled(
        self, mocker, monkeypatch, mock_env_vars
    ):
        """Aggregation failure should notify when configured."""
        details = [
            RateDetail(
                source="openexchangerates",
                pair="EUR/USD",
                status="error",
                error="network timeout",
            )
        ]

        monkeypatch.setenv("NOTIFY_ON_AGGREGATION_FAILURE", "true")

        mocker.patch("script.get_aggregation_method", return_value="median")
        mocker.patch(
            "script.get_enabled_provider_names", return_value=["openexchangerates"]
        )
        mocker.patch("script.get_min_successful_sources", return_value=1)
        mocker.patch("script.validate_min_successful_sources", return_value=None)
        mocker.patch("script.fetch_rate_details", return_value=details)
        mocker.patch(
            "script.aggregate_rate_details",
            side_effect=ValueError("Not enough successful sources"),
        )
        mock_notify = mocker.patch("script.notify")

        with pytest.raises(ValueError, match="Not enough successful sources"):
            check_and_notify()

        mock_notify.assert_called_once()
        subject, message = mock_notify.call_args[0]
        assert "Aggregation failed" in subject
        assert "Not enough successful sources" in message
