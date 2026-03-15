"""Tests for calculate_grade() function."""

import pytest
from datetime import datetime
from config.settings import calculate_grade


class TestCalculateGrade:
    """Test grade calculation from reference point."""

    def test_leona_reference_point(self):
        """Leona: Grade 5 in 2025-2026 school year."""
        # During reference school year
        assert calculate_grade(2025, 5, datetime(2026, 3, 15)) == 5
        assert calculate_grade(2025, 5, datetime(2026, 6, 15)) == 5
        assert calculate_grade(2025, 5, datetime(2026, 7, 15)) == 5
        
        # After school year transition (August 2026)
        assert calculate_grade(2025, 5, datetime(2026, 8, 15)) == 6
        assert calculate_grade(2025, 5, datetime(2026, 9, 15)) == 6

    def test_leona_grade_progression(self):
        """Test Leona's grade progression over multiple years."""
        assert calculate_grade(2025, 5, datetime(2026, 3, 15)) == 5   # 2025-2026
        assert calculate_grade(2025, 5, datetime(2027, 3, 15)) == 6   # 2026-2027
        assert calculate_grade(2025, 5, datetime(2028, 3, 15)) == 7   # 2027-2028
        assert calculate_grade(2025, 5, datetime(2029, 3, 15)) == 8   # 2028-2029

    def test_leonidas_reference_point(self):
        """Leonidas: Grade 1 in 2025-2026 school year."""
        # During reference school year
        assert calculate_grade(2025, 1, datetime(2026, 3, 15)) == 1
        assert calculate_grade(2025, 1, datetime(2026, 6, 15)) == 1
        assert calculate_grade(2025, 1, datetime(2026, 7, 15)) == 1
        
        # After school year transition (August 2026)
        assert calculate_grade(2025, 1, datetime(2026, 8, 15)) == 2
        assert calculate_grade(2025, 1, datetime(2026, 9, 15)) == 2

    def test_leonidas_grade_progression(self):
        """Test Leonidas's grade progression over multiple years."""
        assert calculate_grade(2025, 1, datetime(2026, 3, 15)) == 1   # 2025-2026
        assert calculate_grade(2025, 1, datetime(2027, 3, 15)) == 2   # 2026-2027
        assert calculate_grade(2025, 1, datetime(2028, 3, 15)) == 3   # 2027-2028
        assert calculate_grade(2025, 1, datetime(2029, 3, 15)) == 4   # 2028-2029

    def test_grade_clamping_minimum(self):
        """Test that grade doesn't go below 1."""
        # Reference grade 1, but date is 5 years before reference
        assert calculate_grade(2025, 1, datetime(2020, 3, 15)) == 1

    def test_grade_clamping_maximum(self):
        """Test that grade doesn't go above 12."""
        # Reference grade 5, but date is 20 years after reference
        assert calculate_grade(2025, 5, datetime(2045, 3, 15)) == 12

    def test_grade_default_date(self):
        """Test that calculate_grade uses current date when not specified."""
        # Should not raise an exception and should return valid grade
        result = calculate_grade(2025, 5)
        assert isinstance(result, int)
        assert 1 <= result <= 12

    def test_same_school_year_no_change(self):
        """Test that grade doesn't change within same school year."""
        # All these dates are in 2025-2026 school year
        grade_mar = calculate_grade(2025, 5, datetime(2026, 3, 15))
        grade_jun = calculate_grade(2025, 5, datetime(2026, 6, 15))
        grade_jul = calculate_grade(2025, 5, datetime(2026, 7, 15))
        
        assert grade_mar == grade_jun == grade_jul == 5

    def test_school_year_transition_august(self):
        """Test grade increases in August (school year transition)."""
        grade_july = calculate_grade(2025, 5, datetime(2026, 7, 15))
        grade_august = calculate_grade(2025, 5, datetime(2026, 8, 15))
        
        assert grade_august == grade_july + 1
