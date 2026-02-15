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
        "TARGET_CURRENCY": "EUR",
        "COMPARISON_CURRENCY": "USD",
        "THRESHOLD_RATE": "0.9",
        "MAILGUN_DOMAIN": "test.mailgun.org",
        "MAILGUN_API_KEY": "test_api_key",
        "MAILGUN_FROM": "from@test.com",
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
