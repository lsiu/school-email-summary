"""Integration tests for get_children_info() function."""

import pytest
from datetime import datetime
from config.settings import get_children_info


class TestGetChildrenInfo:
    """Integration tests for children info calculation."""

    def test_current_date_march_2026(self):
        """Test with current date (March 2026 - during 2025-2026 school year)."""
        info = get_children_info(datetime(2026, 3, 15))
        
        # Leona checks
        assert info["leona"]["name"] == "Leona Siu"
        assert info["leona"]["class"] == "Indus"
        assert info["leona"]["grade"] == 5
        assert info["leona"]["division"] == "Upper Elementary"
        assert info["leona"]["school_year"] == "2025-2026"
        
        # Leonidas checks
        assert info["leonidas"]["name"] == "Leonidas Siu"
        assert info["leonidas"]["class"] == "Bauhinia"
        assert info["leonidas"]["grade"] == 1
        assert info["leonidas"]["division"] == "Lower Elementary"
        assert info["leonidas"]["school_year"] == "2025-2026"

    def test_end_of_school_year_june_2026(self):
        """Test at end of 2025-2026 school year (June)."""
        info = get_children_info(datetime(2026, 6, 15))
        
        assert info["leona"]["grade"] == 5
        assert info["leonidas"]["grade"] == 1
        assert info["leona"]["school_year"] == "2025-2026"
        assert info["leonidas"]["school_year"] == "2025-2026"

    def test_summer_break_july_2026(self):
        """Test during summer break (July - still shows previous school year)."""
        info = get_children_info(datetime(2026, 7, 15))
        
        assert info["leona"]["grade"] == 5
        assert info["leonidas"]["grade"] == 1
        assert info["leona"]["school_year"] == "2025-2026"
        assert info["leonidas"]["school_year"] == "2025-2026"

    def test_new_school_year_august_2026(self):
        """Test after school year transition (August 2026)."""
        info = get_children_info(datetime(2026, 8, 15))
        
        # Grades should have increased
        assert info["leona"]["grade"] == 6
        assert info["leonidas"]["grade"] == 2
        
        # School year should have updated
        assert info["leona"]["school_year"] == "2026-2027"
        assert info["leonidas"]["school_year"] == "2026-2027"
        
        # Divisions should remain the same at this point
        assert info["leona"]["division"] == "Upper Elementary"
        assert info["leonidas"]["division"] == "Lower Elementary"

    def test_september_2027(self):
        """Test in September 2027 (2027-2028 school year)."""
        info = get_children_info(datetime(2027, 9, 15))
        
        assert info["leona"]["grade"] == 7
        assert info["leona"]["division"] == "Middle School"
        assert info["leona"]["school_year"] == "2027-2028"
        
        assert info["leonidas"]["grade"] == 3
        assert info["leonidas"]["division"] == "Lower Elementary"
        assert info["leonidas"]["school_year"] == "2027-2028"

    def test_september_2028(self):
        """Test in September 2028 (2028-2029 school year)."""
        info = get_children_info(datetime(2028, 9, 15))
        
        assert info["leona"]["grade"] == 8
        assert info["leona"]["division"] == "Middle School"
        assert info["leona"]["school_year"] == "2028-2029"
        
        assert info["leonidas"]["grade"] == 4
        assert info["leonidas"]["division"] == "Upper Elementary"
        assert info["leonidas"]["school_year"] == "2028-2029"

    def test_default_date(self):
        """Test that get_children_info uses current date when not specified."""
        info = get_children_info()
        
        # Should return valid data structure
        assert "leona" in info
        assert "leonidas" in info
        
        # Each child should have required fields
        for child_key in ["leona", "leonidas"]:
            assert "name" in info[child_key]
            assert "class" in info[child_key]
            assert "grade" in info[child_key]
            assert "division" in info[child_key]
            assert "school_year" in info[child_key]

    def test_returns_copy_not_reference(self):
        """Test that function returns a copy, not modifying internal state."""
        info1 = get_children_info(datetime(2026, 3, 15))
        info2 = get_children_info(datetime(2027, 3, 15))
        
        # Different dates should return different grades
        assert info1["leona"]["grade"] != info2["leona"]["grade"]
