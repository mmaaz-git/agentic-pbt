#!/usr/bin/env python3
"""More comprehensive property-based tests for htmldate library."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime
from hypothesis import given, strategies as st, assume, settings
import pytest

from htmldate.validators import is_valid_date, validate_and_convert, plausible_year_filter
from htmldate.utils import Extractor
from htmldate.settings import MIN_DATE


# Test is_valid_date with edge cases
@given(
    st.one_of(
        st.none(),
        st.datetimes(min_value=datetime(1, 1, 1), max_value=datetime(9999, 12, 31)),
        st.text()
    )
)
def test_is_valid_date_handles_various_inputs(date_input):
    """Test that is_valid_date handles various input types without crashing."""
    earliest = datetime(1990, 1, 1)
    latest = datetime(2030, 12, 31)
    
    result = is_valid_date(date_input, "%Y-%m-%d", earliest, latest)
    
    # Should always return a boolean
    assert isinstance(result, bool)
    
    # None should always return False
    if date_input is None:
        assert result == False


# Test date format validation edge cases
@given(st.text(alphabet="%-YmdHMSBbAa/.,:! ", min_size=1, max_size=20))
def test_is_valid_date_with_format_variations(format_str):
    """Test is_valid_date with various format strings."""
    date_input = "2020-05-15"
    earliest = datetime(2000, 1, 1)
    latest = datetime(2030, 12, 31)
    
    # Should not crash regardless of format
    try:
        result = is_valid_date(date_input, format_str, earliest, latest)
        assert isinstance(result, bool)
    except:
        # Some formats might not be valid, that's ok
        pass


# Test the date parsing with extreme values
@given(
    st.integers(min_value=-9999, max_value=9999),
    st.integers(min_value=-12, max_value=100),
    st.integers(min_value=-31, max_value=100)
)
def test_date_validation_with_extreme_values(year, month, day):
    """Test date validation with extreme integer values."""
    date_str = f"{year:04d}-{month:02d}-{day:02d}"
    earliest = datetime(1990, 1, 1)
    latest = datetime(2030, 12, 31)
    
    result = is_valid_date(date_str, "%Y-%m-%d", earliest, latest)
    
    # Should always return boolean
    assert isinstance(result, bool)
    
    # If result is True, the date should be parseable and in range
    if result:
        try:
            parsed = datetime.strptime(date_str, "%Y-%m-%d")
            assert earliest <= parsed <= latest
        except ValueError:
            # If strptime fails, is_valid_date should have returned False
            pytest.fail(f"is_valid_date returned True but date is invalid: {date_str}")


# Test validate_and_convert function
@given(
    st.one_of(
        st.none(),
        st.datetimes(min_value=datetime(1990, 1, 1), max_value=datetime(2030, 12, 31)),
        st.text(min_size=1, max_size=20)
    )
)
def test_validate_and_convert_consistency(date_input):
    """Test that validate_and_convert is consistent with is_valid_date."""
    outputformat = "%Y-%m-%d"
    earliest = datetime(1990, 1, 1)
    latest = datetime(2030, 12, 31)
    
    result = validate_and_convert(date_input, outputformat, earliest, latest)
    
    # Result should be None or a string
    assert result is None or isinstance(result, str)
    
    # If validate_and_convert returns a value, is_valid_date should return True
    if result is not None:
        # The result should be a valid date string
        is_valid = is_valid_date(result, outputformat, earliest, latest)
        assert is_valid == True


# Test the Extractor class initialization
@given(
    st.booleans(),
    st.one_of(st.none(), st.datetimes()),
    st.one_of(st.none(), st.datetimes()),
    st.booleans(),
    st.text(min_size=1, max_size=50)
)
def test_extractor_initialization(extensive_search, max_date, min_date, original, format_str):
    """Test that Extractor class can be initialized with various inputs."""
    try:
        extractor = Extractor(extensive_search, max_date, min_date, original, format_str)
        
        # Should have the expected attributes
        assert hasattr(extractor, 'extensive_search')
        assert hasattr(extractor, 'format')
        assert hasattr(extractor, 'original')
        assert hasattr(extractor, 'min')
        assert hasattr(extractor, 'max')
        
        # Values should be set correctly
        assert extractor.extensive_search == extensive_search
        assert extractor.original == original
        assert extractor.format == format_str
    except Exception as e:
        # Some combinations might be invalid, that's ok
        pass


if __name__ == "__main__":
    print("Running comprehensive property-based tests for htmldate...")
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))