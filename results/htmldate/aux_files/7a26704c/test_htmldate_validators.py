import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

import logging
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, assume, settings
import math

# Import the validators module
from htmldate import validators
from htmldate.settings import MIN_DATE

# Configure logging
logging.basicConfig(level=logging.ERROR)

# Strategy for valid datetime format strings
def valid_strftime_formats():
    """Generate valid strftime format strings"""
    directives = ['%Y', '%m', '%d', '%H', '%M', '%S', '%y', '%b', '%B', '%a', '%A']
    separators = ['-', '/', ' ', ':', 'T', '.']
    
    # Generate format strings with 1-3 directives
    return st.builds(
        lambda parts, seps: ''.join(
            p + (s if i < len(seps) else '') 
            for i, p in enumerate(parts)
        ),
        st.lists(st.sampled_from(directives), min_size=1, max_size=3),
        st.lists(st.sampled_from(separators), min_size=0, max_size=2)
    )

# Strategy for generating dates within reasonable bounds
def reasonable_dates():
    """Generate dates between 1995 and now"""
    min_timestamp = MIN_DATE.timestamp()
    max_timestamp = datetime.now().timestamp()
    return st.builds(
        datetime.fromtimestamp,
        st.floats(min_value=min_timestamp, max_value=max_timestamp)
    )

# Test 1: convert_date round-trip property
@given(
    date=reasonable_dates(),
    format_str=valid_strftime_formats()
)
@settings(max_examples=500)
def test_convert_date_round_trip(date, format_str):
    """If inputformat == outputformat, convert_date should return unchanged string"""
    try:
        # Create a date string in the given format
        date_string = date.strftime(format_str)
        
        # Test the property: same input/output format returns unchanged
        result = validators.convert_date(date_string, format_str, format_str)
        assert result == date_string, f"Round-trip failed: {date_string} != {result}"
    except (ValueError, TypeError):
        # Skip invalid format combinations
        pass

# Test 2: is_valid_format property
@given(format_str=valid_strftime_formats())
@settings(max_examples=500)
def test_is_valid_format_accepts_valid_formats(format_str):
    """Valid strftime format strings should be accepted by is_valid_format"""
    result = validators.is_valid_format(format_str)
    assert result == True, f"Valid format {format_str} was rejected"

@given(
    invalid_format=st.one_of(
        st.text(min_size=1, max_size=20).filter(lambda x: '%' not in x),
        st.just(''),
        st.just('%'),
        st.just('%%'),
    )
)
@settings(max_examples=500)
def test_is_valid_format_rejects_invalid_formats(invalid_format):
    """Invalid format strings should be rejected"""
    result = validators.is_valid_format(invalid_format)
    # Formats without % should be rejected (except %% which is valid)
    if '%' not in invalid_format or invalid_format == '%':
        assert result == False, f"Invalid format {invalid_format} was accepted"

# Test 3: is_valid_date boundary testing
@given(
    year=st.integers(min_value=1900, max_value=2200),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),  # Avoid month-end issues
)
@settings(max_examples=500)
def test_is_valid_date_respects_bounds(year, month, day):
    """is_valid_date should properly validate dates within bounds"""
    # Create a test date
    test_date = datetime(year, month, day)
    date_string = test_date.strftime("%Y-%m-%d")
    
    # Set boundaries
    earliest = datetime(year - 10, 1, 1)
    latest = datetime(year + 10, 12, 31)
    
    # Test that dates within bounds are valid
    result = validators.is_valid_date(date_string, "%Y-%m-%d", earliest, latest)
    assert result == True, f"Date {date_string} should be valid within bounds"
    
    # Test that dates outside bounds are invalid
    earliest_outside = datetime(year + 1, 1, 1)
    result_outside = validators.is_valid_date(date_string, "%Y-%m-%d", earliest_outside, latest)
    assert result_outside == False, f"Date {date_string} should be invalid with earliest={earliest_outside}"
    
    latest_outside = datetime(year - 1, 12, 31)
    result_outside2 = validators.is_valid_date(date_string, "%Y-%m-%d", earliest, latest_outside)
    assert result_outside2 == False, f"Date {date_string} should be invalid with latest={latest_outside}"

# Test 4: check_date_input ISO format handling
@given(
    date=reasonable_dates()
)
@settings(max_examples=500)
def test_check_date_input_iso_format(date):
    """check_date_input should correctly parse ISO format strings"""
    # Create ISO format string
    iso_string = date.isoformat()
    
    # Default datetime for fallback
    default = datetime(2000, 1, 1)
    
    # Test the function
    result = validators.check_date_input(iso_string, default)
    
    # The result should match the original date (within microsecond precision)
    assert abs((result - date).total_seconds()) < 1, f"ISO parsing failed: {iso_string} -> {result} != {date}"

@given(
    invalid_input=st.one_of(
        st.text(min_size=1, max_size=20),
        st.just("not-a-date"),
        st.just("2024-13-01"),  # Invalid month
        st.just("2024-01-32"),  # Invalid day
    )
)
@settings(max_examples=500)
def test_check_date_input_returns_default_for_invalid(invalid_input):
    """check_date_input should return default for invalid inputs"""
    default = datetime(2000, 1, 1)
    
    # Filter out accidentally valid ISO strings
    try:
        datetime.fromisoformat(invalid_input)
        # Skip if accidentally valid
        assume(False)
    except (ValueError, AttributeError):
        pass
    
    result = validators.check_date_input(invalid_input, default)
    assert result == default, f"Should return default for invalid input {invalid_input}"

# Test 5: get_min_date/get_max_date default handling
@given(
    invalid_input=st.one_of(
        st.none(),
        st.text(min_size=1, max_size=20).filter(lambda x: not x.startswith('20')),
        st.just("invalid"),
    )
)
@settings(max_examples=500)
def test_get_min_date_returns_default_for_invalid(invalid_input):
    """get_min_date should return MIN_DATE for invalid inputs"""
    result = validators.get_min_date(invalid_input)
    assert result == MIN_DATE, f"Should return MIN_DATE for invalid input {invalid_input}"

@given(
    invalid_input=st.one_of(
        st.none(),
        st.text(min_size=1, max_size=20).filter(lambda x: not x.startswith('20')),
        st.just("invalid"),
    )
)
@settings(max_examples=500)
def test_get_max_date_returns_default_for_invalid(invalid_input):
    """get_max_date should return datetime.now() for invalid inputs"""
    before = datetime.now()
    result = validators.get_max_date(invalid_input)
    after = datetime.now()
    
    # Result should be close to now (within a second)
    assert before <= result <= after + timedelta(seconds=1), f"Should return near datetime.now() for invalid input {invalid_input}"

# Test 6: Additional property - validate_and_convert consistency
@given(
    date=reasonable_dates(),
    outputformat=st.sampled_from(["%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y", "%Y%m%d"])
)
@settings(max_examples=500)
def test_validate_and_convert_consistency(date, outputformat):
    """validate_and_convert should be consistent with is_valid_date"""
    date_string = date.strftime("%Y-%m-%d")
    earliest = datetime(1990, 1, 1)
    latest = datetime(2030, 12, 31)
    
    # If is_valid_date returns True, validate_and_convert should return non-None
    is_valid = validators.is_valid_date(date_string, "%Y-%m-%d", earliest, latest)
    result = validators.validate_and_convert(date_string, outputformat, earliest, latest)
    
    if is_valid:
        assert result is not None, f"validate_and_convert returned None for valid date {date_string}"
    else:
        assert result is None, f"validate_and_convert returned {result} for invalid date {date_string}"

# Test 7: Edge case - convert_date with datetime objects
@given(date=reasonable_dates(), outputformat=valid_strftime_formats())
@settings(max_examples=500)
def test_convert_date_datetime_input(date, outputformat):
    """convert_date should handle datetime objects directly"""
    try:
        result = validators.convert_date(date, "%Y-%m-%d", outputformat)
        expected = date.strftime(outputformat)
        assert result == expected, f"DateTime conversion failed: {result} != {expected}"
    except (ValueError, TypeError):
        # Skip invalid format combinations
        pass