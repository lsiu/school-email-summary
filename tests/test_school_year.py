"""Tests for get_school_year() function."""

import pytest
from datetime import datetime
from config.settings import get_school_year


class TestGetSchoolYear:
    """Test school year calculation from dates."""

    @pytest.mark.parametrize("date,expected", [
        # School year 2025-2026
        (datetime(2026, 1, 15), 2025),    # January: in 2025-2026 SY
        (datetime(2026, 2, 28), 2025),    # February: in 2025-2026 SY
        (datetime(2026, 3, 15), 2025),    # March: in 2025-2026 SY (current)
        (datetime(2026, 4, 15), 2025),    # April: in 2025-2026 SY
        (datetime(2026, 5, 15), 2025),    # May: in 2025-2026 SY
        (datetime(2026, 6, 15), 2025),    # June: end of 2025-2026 SY
        (datetime(2026, 7, 15), 2025),    # July: summer break (still 2025-2026)
        
        # School year 2026-2027
        (datetime(2026, 8, 1), 2026),     # August 1: start of 2026-2027 SY
        (datetime(2026, 8, 15), 2026),    # August: in 2026-2027 SY
        (datetime(2026, 9, 15), 2026),    # September: in 2026-2027 SY
        (datetime(2026, 10, 15), 2026),   # October: in 2026-2027 SY
        (datetime(2026, 11, 15), 2026),   # November: in 2026-2027 SY
        (datetime(2026, 12, 15), 2026),   # December: in 2026-2027 SY
    ])
    def test_school_year_boundaries(self, date, expected):
        """Test that school year is correctly determined for each month."""
        assert get_school_year(date) == expected

    def test_school_year_default_date(self):
        """Test that get_school_year uses current date when not specified."""
        # Should not raise an exception
        result = get_school_year()
        assert isinstance(result, int)
        assert result >= 2025  # Reasonable minimum

    def test_school_year_format(self):
        """Test that school year returns an integer."""
        result = get_school_year(datetime(2026, 3, 15))
        assert isinstance(result, int)
