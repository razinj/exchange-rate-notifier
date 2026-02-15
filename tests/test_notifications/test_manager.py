"""Tests for the notifications manager module."""

from unittest.mock import MagicMock

import pytest  # noqa: F401

from notifications.manager import (
    _build_gotify_url,
    _build_mailgun_url,
    get_notification_manager,
    notify,
)


class TestBuildMailgunUrl:
    """Tests for _build_mailgun_url function."""

    def test_returns_url_when_all_vars_set(self, monkeypatch):
        """Test URL built when all Mailgun env vars present."""
        # Arrange
        monkeypatch.setenv("MAILGUN_DOMAIN", "test.mailgun.org")
        monkeypatch.setenv("MAILGUN_API_KEY", "test_key")
        monkeypatch.setenv("MAILGUN_FROM", "from@test.com")
        monkeypatch.setenv("MAILGUN_TO", "to@test.com")

        # Act
        result = _build_mailgun_url()

        # Assert
        assert (
            result
            == "mailgun://test.mailgun.org/test_key?from=from@test.com&to=to@test.com"
        )

    def test_returns_none_when_missing_vars(self, monkeypatch):
        """Test returns None when Mailgun vars missing."""
        # Arrange
        monkeypatch.delenv("MAILGUN_API_KEY", raising=False)

        # Act
        result = _build_mailgun_url()

        # Assert
        assert result is None

    def test_returns_none_when_empty_vars(self, monkeypatch):
        """Test returns None when Mailgun vars are empty strings."""
        # Arrange
        monkeypatch.setenv("MAILGUN_DOMAIN", "")
        monkeypatch.setenv("MAILGUN_API_KEY", "test_key")
        monkeypatch.setenv("MAILGUN_FROM", "from@test.com")
        monkeypatch.setenv("MAILGUN_TO", "to@test.com")

        # Act
        result = _build_mailgun_url()

        # Assert
        assert result is None


class TestBuildGotifyUrl:
    """Tests for _build_gotify_url function."""

    def test_returns_https_url(self, monkeypatch):
        """Test HTTPS URL built correctly."""
        # Arrange
        monkeypatch.setenv("GOTIFY_URL", "https://gotify.example.com")
        monkeypatch.setenv("GOTIFY_TOKEN", "abc123")

        # Act
        result = _build_gotify_url()

        # Assert
        assert result == "gotifys://gotify.example.com/abc123"

    def test_returns_http_url(self, monkeypatch):
        """Test HTTP URL built correctly."""
        # Arrange
        monkeypatch.setenv("GOTIFY_URL", "http://gotify.local")
        monkeypatch.setenv("GOTIFY_TOKEN", "abc123")

        # Act
        result = _build_gotify_url()

        # Assert
        assert result == "gotify://gotify.local/abc123"

    def test_defaults_to_https(self, monkeypatch):
        """Test defaults to HTTPS when no protocol specified."""
        # Arrange
        monkeypatch.setenv("GOTIFY_URL", "gotify.example.com")
        monkeypatch.setenv("GOTIFY_TOKEN", "abc123")

        # Act
        result = _build_gotify_url()

        # Assert
        assert result == "gotifys://gotify.example.com/abc123"

    def test_returns_none_when_missing_url(self, monkeypatch):
        """Test returns None when Gotify URL is missing."""
        # Arrange
        monkeypatch.delenv("GOTIFY_URL", raising=False)
        monkeypatch.setenv("GOTIFY_TOKEN", "abc123")

        # Act
        result = _build_gotify_url()

        # Assert
        assert result is None

    def test_returns_none_when_missing_token(self, monkeypatch):
        """Test returns None when Gotify token is missing."""
        # Arrange
        monkeypatch.setenv("GOTIFY_URL", "https://gotify.example.com")
        monkeypatch.delenv("GOTIFY_TOKEN", raising=False)

        # Act
        result = _build_gotify_url()

        # Assert
        assert result is None


class TestGetNotificationManager:
    """Tests for get_notification_manager function."""

    def test_configures_mailgun_when_enabled(self, mocker, monkeypatch):
        """Test Mailgun added when env vars set."""
        # Arrange
        monkeypatch.setenv("MAILGUN_DOMAIN", "test.mailgun.org")
        monkeypatch.setenv("MAILGUN_API_KEY", "test_key")
        monkeypatch.setenv("MAILGUN_FROM", "from@test.com")
        monkeypatch.setenv("MAILGUN_TO", "to@test.com")

        mock_apprise = mocker.patch("src.notifications.manager.apprise.Apprise")
        mock_instance = MagicMock()
        mock_apprise.return_value = mock_instance

        # Act
        get_notification_manager()

        # Assert
        mock_instance.add.assert_called_once()
        assert "mailgun://" in mock_instance.add.call_args[0][0]

    def test_configures_gotify_when_enabled(self, mocker, monkeypatch):
        """Test Gotify added when env vars set."""
        # Arrange
        monkeypatch.setenv("GOTIFY_URL", "https://gotify.example.com")
        monkeypatch.setenv("GOTIFY_TOKEN", "abc123")

        mock_apprise = mocker.patch("src.notifications.manager.apprise.Apprise")
        mock_instance = MagicMock()
        mock_apprise.return_value = mock_instance

        # Act
        get_notification_manager()

        # Assert
        mock_instance.add.assert_called_once()
        assert "gotifys://" in mock_instance.add.call_args[0][0]

    def test_configures_both_when_enabled(self, mocker, monkeypatch):
        """Test both Mailgun and Gotify added when both enabled."""
        # Arrange
        monkeypatch.setenv("MAILGUN_DOMAIN", "test.mailgun.org")
        monkeypatch.setenv("MAILGUN_API_KEY", "test_key")
        monkeypatch.setenv("MAILGUN_FROM", "from@test.com")
        monkeypatch.setenv("MAILGUN_TO", "to@test.com")
        monkeypatch.setenv("GOTIFY_URL", "https://gotify.example.com")
        monkeypatch.setenv("GOTIFY_TOKEN", "abc123")

        mock_apprise = mocker.patch("src.notifications.manager.apprise.Apprise")
        mock_instance = MagicMock()
        mock_apprise.return_value = mock_instance

        # Act
        get_notification_manager()

        # Assert
        assert mock_instance.add.call_count == 2

    def test_no_targets_when_no_env_vars(self, mocker, monkeypatch):
        """Test no targets added when no env vars set."""
        # Arrange
        monkeypatch.delenv("MAILGUN_DOMAIN", raising=False)
        monkeypatch.delenv("GOTIFY_URL", raising=False)

        mock_apprise = mocker.patch("src.notifications.manager.apprise.Apprise")
        mock_instance = MagicMock()
        mock_apprise.return_value = mock_instance

        # Act
        get_notification_manager()

        # Assert
        mock_instance.add.assert_not_called()


class TestNotify:
    """Tests for notify function."""

    def test_sends_notification_successfully(self, mocker):
        """Test notify sends notification and returns True."""
        # Arrange
        mock_apprise = mocker.patch("src.notifications.manager.apprise.Apprise")
        mock_instance = MagicMock()
        mock_instance.notify.return_value = True
        mock_apprise.return_value = mock_instance

        # Act
        result = notify("Test Subject", "Test Body")

        # Assert
        assert result is True
        mock_instance.notify.assert_called_once_with(
            body="Test Body", title="Test Subject"
        )

    def test_returns_false_when_no_targets(self, mocker):
        """Test returns False when no notification targets configured."""
        # Arrange
        mock_get_manager = mocker.patch(
            "src.notifications.manager.get_notification_manager"
        )
        mock_get_manager.return_value = None

        # Act
        result = notify("Test Subject", "Test Body")

        # Assert
        assert result is False

    def test_returns_false_on_failure(self, mocker):
        """Test returns False when notification fails."""
        # Arrange
        mock_apprise = mocker.patch("src.notifications.manager.apprise.Apprise")
        mock_instance = MagicMock()
        mock_instance.notify.return_value = False
        mock_apprise.return_value = mock_instance

        # Act
        result = notify("Test Subject", "Test Body")

        # Assert
        assert result is False
