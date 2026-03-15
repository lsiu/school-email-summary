"""Tests for get_division() and get_division_range() functions."""

import pytest
from config.settings import get_division, get_division_range


class TestGetDivision:
    """Test grade to division mapping."""

    @pytest.mark.parametrize("grade,expected", [
        # Lower Elementary (Grades 1-3)
        (1, "Lower Elementary"),
        (2, "Lower Elementary"),
        (3, "Lower Elementary"),
        
        # Upper Elementary (Grades 4-6)
        (4, "Upper Elementary"),
        (5, "Upper Elementary"),
        (6, "Upper Elementary"),
        
        # Middle School (Grades 7-8)
        (7, "Middle School"),
        (8, "Middle School"),
        
        # Outside elementary/middle range
        (9, "Unknown Division"),
        (10, "Unknown Division"),
        (12, "Unknown Division"),
    ])
    def test_division_mapping(self, grade, expected):
        """Test that each grade maps to the correct division."""
        assert get_division(grade) == expected

    def test_division_boundary_lower_to_upper(self):
        """Test division boundary between Lower and Upper Elementary."""
        assert get_division(3) == "Lower Elementary"
        assert get_division(4) == "Upper Elementary"

    def test_division_boundary_upper_to_middle(self):
        """Test division boundary between Upper Elementary and Middle School."""
        assert get_division(6) == "Upper Elementary"
        assert get_division(7) == "Middle School"

    def test_division_middle_school_boundary(self):
        """Test division boundary at end of Middle School."""
        assert get_division(8) == "Middle School"
        assert get_division(9) == "Unknown Division"


class TestGetDivisionRange:
    """Test division to grade range mapping."""

    @pytest.mark.parametrize("division,expected", [
        ("Lower Elementary", "Grades 1-3"),
        ("Upper Elementary", "Grades 4-6"),
        ("Middle School", "Grades 7-8"),
    ])
    def test_division_range(self, division, expected):
        """Test that each division maps to the correct grade range."""
        assert get_division_range(division) == expected

    def test_division_range_unknown(self):
        """Test unknown division returns unknown range."""
        assert get_division_range("Unknown Division") == "Unknown Grades"
        assert get_division_range("High School") == "Unknown Grades"

    def test_division_range_case_sensitive(self):
        """Test that division names are case-sensitive."""
        # Should not match due to case difference
        assert get_division_range("lower elementary") == "Unknown Grades"
        assert get_division_range("LOWER ELEMENTARY") == "Unknown Grades"


class TestDivisionConsistency:
    """Test consistency between get_division and get_division_range."""

    @pytest.mark.parametrize("grade,division,range_str", [
        (1, "Lower Elementary", "Grades 1-3"),
        (3, "Lower Elementary", "Grades 1-3"),
        (4, "Upper Elementary", "Grades 4-6"),
        (6, "Upper Elementary", "Grades 4-6"),
        (7, "Middle School", "Grades 7-8"),
        (8, "Middle School", "Grades 7-8"),
    ])
    def test_division_and_range_consistency(self, grade, division, range_str):
        """Test that division and range are consistent for each grade."""
        assert get_division(grade) == division
        assert get_division_range(division) == range_str
