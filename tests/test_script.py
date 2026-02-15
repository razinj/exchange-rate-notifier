"""Tests for the main script module."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from script import check_and_notify, fetch_exchange_rates, prepare_inputs


class TestFetchExchangeRates:
    """Tests for fetch_exchange_rates function."""

    @patch("script.httpx.get")
    def test_successful_fetch(self, mock_get, mock_env_vars):
        """Test successful API call returns exchange rates."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": {"EUR": 0.92}}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        result = fetch_exchange_rates()

        # Assert
        assert "rates" in result
        assert result["rates"]["EUR"] == 0.92
        mock_get.assert_called_once()

    @patch("script.httpx.get")
    def test_api_error_raises_exception(self, mock_get, mock_env_vars):
        """Test that API errors raise exceptions."""
        # Arrange
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=MagicMock()
        )
        mock_get.return_value = mock_response

        # Act & Assert
        with pytest.raises(httpx.HTTPStatusError):
            fetch_exchange_rates()


class TestPrepareInputs:
    """Tests for prepare_inputs function."""

    def test_valid_inputs(self, mock_env_vars):
        """Test valid inputs are parsed correctly."""
        # Act
        threshold, target, comparison = prepare_inputs()

        # Assert
        assert threshold == 0.9
        assert target == "EUR"
        assert comparison == "USD"

    def test_negative_threshold_raises_error(self, monkeypatch, mock_env_vars):
        """Test that negative threshold raises ValueError."""
        # Arrange
        monkeypatch.setenv("THRESHOLD_RATE", "-1.0")

        # Act & Assert
        with pytest.raises(ValueError, match="positive number"):
            prepare_inputs()


class TestCheckAndNotify:
    """Tests for check_and_notify function."""

    def test_notifies_when_threshold_met(self, mocker, mock_env_vars):
        """Test notification sent when rate >= threshold."""
        # Arrange
        mocker.patch(
            "script.fetch_exchange_rates",
            return_value={"rates": {"EUR": 0.95, "USD": 1.0}},
        )
        mock_notify = mocker.patch("script.notify")

        # Act
        check_and_notify()

        # Assert
        mock_notify.assert_called_once()
        # Check that the notification message contains the rate
        call_args = mock_notify.call_args
        assert "0.95" in call_args[0][0] or "0.95" in call_args[1].get("body", "")

    def test_no_notification_when_below_threshold(self, mocker, mock_env_vars):
        """Test no notification when rate < threshold."""
        # Arrange
        mocker.patch(
            "script.fetch_exchange_rates",
            return_value={"rates": {"EUR": 0.80, "USD": 1.0}},
        )
        mock_notify = mocker.patch("script.notify")
        mock_print = mocker.patch("builtins.print")

        # Act
        check_and_notify()

        # Assert
        mock_notify.assert_not_called()
        # Verify the "below threshold" message was printed
        mock_print.assert_any_call(
            "The current exchange rate 0.80 EUR is below the threshold rate 0.90 EUR."
        )
