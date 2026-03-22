"""Tests for shared HTTP client helpers."""

import httpx
import pytest

from rates.http_client import request_json, sanitize_error_message


class TestRequestJson:
    """Tests for request_json retry behavior."""

    def test_retries_transient_status_then_succeeds(self, mocker, monkeypatch):
        """Transient HTTP status should retry before succeeding."""
        monkeypatch.setenv("HTTP_MAX_RETRIES", "2")
        monkeypatch.setenv("HTTP_BACKOFF_BASE_SECONDS", "0")
        monkeypatch.setenv("HTTP_BACKOFF_MAX_SECONDS", "0")

        request = httpx.Request("GET", "https://example.com/latest")
        first_response = httpx.Response(status_code=503, request=request)
        second_response = httpx.Response(
            status_code=200,
            request=request,
            json={"ok": True},
        )

        mock_get = mocker.patch(
            "rates.http_client.httpx.get",
            side_effect=[first_response, second_response],
        )
        mock_sleep = mocker.patch("rates.http_client.time.sleep")

        payload = request_json("https://example.com/latest")

        assert payload == {"ok": True}
        assert mock_get.call_count == 2
        mock_sleep.assert_not_called()

    def test_does_not_retry_non_transient_status(self, mocker, monkeypatch):
        """Non-transient HTTP status should fail immediately."""
        monkeypatch.setenv("HTTP_MAX_RETRIES", "3")

        request = httpx.Request("GET", "https://example.com/latest")
        response = httpx.Response(status_code=404, request=request)

        mock_get = mocker.patch("rates.http_client.httpx.get", return_value=response)
        mock_sleep = mocker.patch("rates.http_client.time.sleep")

        with pytest.raises(httpx.HTTPStatusError):
            request_json("https://example.com/latest")

        mock_get.assert_called_once()
        mock_sleep.assert_not_called()


class TestSanitizeErrorMessage:
    """Tests for secret redaction in error messages."""

    def test_redacts_common_api_key_patterns(self):
        """Sensitive query/path key values should be removed."""
        raw_message = (
            "Client error for URL "
            "https://v6.exchangerate-api.com/v6/abc123/pair/EUR/MAD"
            "?apikey=myapikey&app_id=myappid&access_key=myaccess"
        )

        sanitized_message = sanitize_error_message(raw_message)

        assert "abc123" not in sanitized_message
        assert "myapikey" not in sanitized_message
        assert "myappid" not in sanitized_message
        assert "myaccess" not in sanitized_message
        assert "<redacted>" in sanitized_message
