"""Tests for rate aggregation helpers."""

import pytest

from rates.aggregation import aggregate_rates


class TestAggregateRates:
    """Tests for aggregate_rates function."""

    def test_median_aggregation(self):
        """Median should resist outlier values."""
        result = aggregate_rates([10.0, 10.1, 10.2, 99.9], "median")

        assert result == 10.149999999999999

    def test_mean_aggregation(self):
        """Mean should average all values."""
        result = aggregate_rates([1.0, 2.0, 3.0], "mean")

        assert result == 2.0

    def test_none_aggregation_is_rejected(self):
        """None mode is no longer a supported aggregation method."""
        with pytest.raises(ValueError, match="Unsupported aggregation method"):
            aggregate_rates([1.5, 1.6, 1.7], "none")

    def test_raises_for_empty_rates(self):
        """Aggregation should fail with no successful sources."""
        with pytest.raises(ValueError, match="At least one successful rate"):
            aggregate_rates([], "median")

    def test_raises_for_unknown_method(self):
        """Unknown method should fail validation."""
        with pytest.raises(ValueError, match="Unsupported aggregation method"):
            aggregate_rates([1.0], "weighted")
