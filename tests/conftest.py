"""Pytest fixtures and configuration."""

import sys
from pathlib import Path

import pytest

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Fixture to set environment variables for testing."""
    env_vars = {
        "OER_APP_ID": "test_app_id",
        "BASE_CURRENCY": "EUR",
        "QUOTE_CURRENCY": "USD",
        "THRESHOLD_RATE": "0.9",
        "RATE_SOURCES": "openexchangerates",
        "AGGREGATION_METHOD": "median",
        "MIN_SUCCESSFUL_SOURCES": "1",
        "BAM_SUBSCRIPTION_KEY": "test_subscription_key",
        "BAM_ENDPOINT": "CoursBBE",
        "EXCHANGERATE_API_KEY": "test_exchangerate_api_key",
        "CURRENCYAPI_API_KEY": "test_currencyapi_api_key",
        "APILAYER_EXCHANGERATESAPI_ACCESS_KEY": "test_apilayer_access_key",
        "FAWAZAHMED0_CURRENCY_API_DATE": "latest",
        "HTTP_TIMEOUT_SECONDS": "12",
        "HTTP_MAX_RETRIES": "2",
        "HTTP_BACKOFF_BASE_SECONDS": "0.5",
        "HTTP_BACKOFF_MAX_SECONDS": "4",
        "NOTIFY_ON_AGGREGATION_FAILURE": "false",
        "MAILGUN_DOMAIN": "test.mailgun.org",
        "MAILGUN_API_KEY": "test_api_key",
        "MAILGUN_TO": "to@test.com",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


@pytest.fixture
def mock_exchange_rate_response():
    """Sample OpenExchangeRate API response."""
    return {
        "disclaimer": "Test data",
        "license": "Test license",
        "timestamp": 1234567890,
        "base": "USD",
        "rates": {
            "EUR": 0.92,
            "USD": 1.0,
            "GBP": 0.79,
        },
    }
