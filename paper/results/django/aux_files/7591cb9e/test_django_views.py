"""Property-based tests for django.views module"""

import django
from django.conf import settings
from hypothesis import given, strategies as st, assume
from django.utils.http import http_date
import time

# Configure Django
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-secret-key',
        USE_TZ=True,
        USE_I18N=True,
        INSTALLED_APPS=['django.contrib.contenttypes'],  # Minimal app for i18n
        ROOT_URLCONF='',
    )
    django.setup()  # Initialize apps

from django.views.static import was_modified_since
from django.views.i18n import get_formats


@given(st.none())
def test_was_modified_since_none_header(header):
    """Test: was_modified_since returns True when header is None (documented behavior)"""
    # Any mtime value should return True when header is None
    assert was_modified_since(header, 0) == True
    assert was_modified_since(header, 1000000) == True
    assert was_modified_since(header, -1) == True


@given(st.integers(min_value=0, max_value=2147483647))
def test_was_modified_since_valid_times(mtime):
    """Test: was_modified_since handles time comparisons correctly"""
    # Create a header from the mtime
    header = http_date(mtime)
    
    # Same time should return False (not modified)
    assert was_modified_since(header, mtime) == False
    
    # Older mtime should return False (not modified)
    if mtime > 0:
        assert was_modified_since(header, mtime - 1) == False
    
    # Newer mtime should return True (was modified)
    if mtime < 2147483647:
        assert was_modified_since(header, mtime + 1) == True


@given(st.text(min_size=1, max_size=100))
def test_was_modified_since_invalid_headers(invalid_header):
    """Test: was_modified_since handles invalid headers gracefully"""
    # Invalid headers should return True (conservative behavior)
    assume(invalid_header != "")  # Empty string handled separately
    
    # Try to ensure it's not a valid HTTP date
    try:
        from django.utils.http import parse_http_date
        parse_http_date(invalid_header)
        # If it's accidentally valid, skip this test case
        assume(False)
    except:
        pass
    
    # Invalid header should return True
    assert was_modified_since(invalid_header, 0) == True
    assert was_modified_since(invalid_header, 1000000) == True


@given(st.floats(allow_nan=True, allow_infinity=True))
def test_was_modified_since_float_mtime(mtime):
    """Test: was_modified_since handles float mtimes correctly"""
    header = http_date(1000000)  # Fixed valid header
    
    # The function should handle float mtimes (converts to int internally)
    try:
        result = was_modified_since(header, mtime)
        # Should return a boolean
        assert isinstance(result, bool)
    except (ValueError, OverflowError):
        # These exceptions are acceptable for extreme floats
        pass


def test_get_formats_structure():
    """Test: get_formats returns consistent dictionary structure"""
    result = get_formats()
    
    # Should return a dictionary
    assert isinstance(result, dict)
    
    # Should contain expected keys
    expected_keys = {
        "DATE_FORMAT",
        "DATETIME_FORMAT", 
        "TIME_FORMAT",
        "YEAR_MONTH_FORMAT",
        "MONTH_DAY_FORMAT",
        "SHORT_DATE_FORMAT",
        "SHORT_DATETIME_FORMAT",
        "FIRST_DAY_OF_WEEK",
        "DECIMAL_SEPARATOR",
        "THOUSAND_SEPARATOR",
        "NUMBER_GROUPING",
        "DATE_INPUT_FORMATS",
        "TIME_INPUT_FORMATS",
        "DATETIME_INPUT_FORMATS",
    }
    
    # All expected keys should be present
    assert expected_keys.issubset(set(result.keys()))
    
    # All values should be non-None
    for key in expected_keys:
        assert result[key] is not None


@given(st.integers(min_value=-2147483648, max_value=2147483647))
def test_was_modified_since_negative_mtime(mtime):
    """Test: was_modified_since handles negative mtimes"""
    header = http_date(0)  # Epoch time header
    
    # Should handle negative mtimes
    result = was_modified_since(header, mtime)
    assert isinstance(result, bool)
    
    # Negative mtime should be older than epoch, so not modified
    if mtime < 0:
        assert result == False
    elif mtime > 0:
        assert result == True
    else:
        assert result == False  # Equal times


@given(st.integers())
def test_was_modified_since_overflow_mtime(mtime):
    """Test: was_modified_since handles overflow in mtime values"""
    header = http_date(1000000)
    
    # Should handle any integer mtime, even those that cause overflow
    result = was_modified_since(header, mtime)
    assert isinstance(result, bool)
    
    # The function behavior:
    # - Returns False if mtime <= header_mtime
    # - Returns True if mtime > header_mtime OR on overflow
    # Negative mtimes are older than positive header times, so should return False
    if mtime <= 1000000:
        assert result == False
    else:
        assert result == True