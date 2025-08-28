#!/usr/bin/env python3
"""
Property-based tests for Google API Core library using Hypothesis.
Testing round-trip properties and invariants in the google.api_core module.
"""

import datetime
import sys
import os

# Add the site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, HealthCheck
import pytest

# Import modules to test
from google.api_core import path_template
from google.api_core import datetime_helpers
from google.api_core import protobuf_helpers


# Test 1: path_template expand/validate round-trip property
@given(
    template=st.text(min_size=1, max_size=100).filter(lambda x: '/' in x or '*' in x or '{' in x),
    args=st.lists(st.text(min_size=1, max_size=50).filter(lambda x: '/' not in x), min_size=0, max_size=5)
)
@settings(max_examples=200, suppress_health_check=[HealthCheck.filter_too_much])
def test_path_template_expand_validate_roundtrip_positional(template, args):
    """Test that expanding a template with positional args and validating returns True."""
    # Count the number of positional variables in template
    import re
    positional_pattern = r'\*\*?(?![}])'
    positional_matches = re.findall(positional_pattern, template)
    num_positional = len(positional_matches)
    
    # Only test if we have the right number of args
    if num_positional != len(args):
        assume(False)
    
    try:
        expanded = path_template.expand(template, *args)
        result = path_template.validate(template, expanded)
        assert result is True, f"validate({template}, expand({template}, {args})) should be True"
    except (ValueError, KeyError, re.error):
        # These are expected errors for invalid templates or insufficient args
        pass


@given(
    variable_name=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=20),
    value=st.text(min_size=1, max_size=50).filter(lambda x: '/' not in x)
)
@settings(max_examples=200) 
def test_path_template_expand_validate_roundtrip_named(variable_name, value):
    """Test that expanding a template with named args and validating returns True."""
    template = f"/v1/{{{variable_name}}}/items"
    kwargs = {variable_name: value}
    
    try:
        expanded = path_template.expand(template, **kwargs)
        result = path_template.validate(template, expanded)
        assert result is True, f"validate({template}, expand({template}, **{kwargs})) should be True"
    except (ValueError, KeyError):
        # These are expected errors for invalid templates
        pass


# Test 2: datetime_helpers microseconds round-trip
@given(
    year=st.integers(min_value=1970, max_value=2100),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),  # Use 28 to avoid month/day issues
    hour=st.integers(min_value=0, max_value=23),
    minute=st.integers(min_value=0, max_value=59),
    second=st.integers(min_value=0, max_value=59),
    microsecond=st.integers(min_value=0, max_value=999999)
)
@settings(max_examples=200)
def test_datetime_microseconds_roundtrip(year, month, day, hour, minute, second, microsecond):
    """Test that converting datetime to microseconds and back preserves the value."""
    dt = datetime.datetime(year, month, day, hour, minute, second, microsecond, 
                          tzinfo=datetime.timezone.utc)
    
    micros = datetime_helpers.to_microseconds(dt)
    dt_reconstructed = datetime_helpers.from_microseconds(micros)
    
    # Both should be timezone-aware and equal
    assert dt == dt_reconstructed, \
        f"from_microseconds(to_microseconds({dt})) should equal {dt}"


@given(micros=st.integers(min_value=0, max_value=10**15))  # Reasonable range for microseconds
@settings(max_examples=200)
def test_microseconds_datetime_roundtrip(micros):
    """Test that converting microseconds to datetime and back preserves the value."""
    dt = datetime_helpers.from_microseconds(micros)
    micros_reconstructed = datetime_helpers.to_microseconds(dt)
    
    assert micros == micros_reconstructed, \
        f"to_microseconds(from_microseconds({micros})) should equal {micros}"


# Test 3: datetime_helpers RFC3339 round-trip
@given(
    year=st.integers(min_value=1970, max_value=2100),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),
    hour=st.integers(min_value=0, max_value=23),
    minute=st.integers(min_value=0, max_value=59),
    second=st.integers(min_value=0, max_value=59),
    microsecond=st.integers(min_value=0, max_value=999999)
)
@settings(max_examples=200)
def test_datetime_rfc3339_roundtrip(year, month, day, hour, minute, second, microsecond):
    """Test that converting datetime to RFC3339 and back preserves the value."""
    dt = datetime.datetime(year, month, day, hour, minute, second, microsecond,
                          tzinfo=datetime.timezone.utc)
    
    rfc3339_str = datetime_helpers.to_rfc3339(dt)
    dt_reconstructed = datetime_helpers.from_rfc3339(rfc3339_str)
    
    assert dt == dt_reconstructed, \
        f"from_rfc3339(to_rfc3339({dt})) should equal {dt}"


@given(
    rfc3339_str=st.from_regex(
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z',
        fullmatch=True
    )
)
@settings(max_examples=200)
def test_rfc3339_string_roundtrip(rfc3339_str):
    """Test that parsing RFC3339 string and converting back preserves format."""
    try:
        dt = datetime_helpers.from_rfc3339(rfc3339_str)
        rfc3339_reconstructed = datetime_helpers.to_rfc3339(dt)
        dt_final = datetime_helpers.from_rfc3339(rfc3339_reconstructed)
        
        # The datetime objects should be equal
        assert dt == dt_final, \
            f"Round-trip through RFC3339 format should preserve datetime value"
    except ValueError:
        # Invalid RFC3339 strings are expected to fail
        pass


# Test 4: DatetimeWithNanoseconds round-trip
@given(
    year=st.integers(min_value=1970, max_value=2100),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),
    hour=st.integers(min_value=0, max_value=23),
    minute=st.integers(min_value=0, max_value=59),
    second=st.integers(min_value=0, max_value=59),
    nanosecond=st.integers(min_value=0, max_value=999999999)
)
@settings(max_examples=200)
def test_datetime_with_nanoseconds_roundtrip(year, month, day, hour, minute, second, nanosecond):
    """Test that DatetimeWithNanoseconds preserves nanosecond precision in round-trip."""
    dt = datetime_helpers.DatetimeWithNanoseconds(
        year, month, day, hour, minute, second, 
        nanosecond=nanosecond, tzinfo=datetime.timezone.utc
    )
    
    rfc3339_str = dt.rfc3339()
    dt_reconstructed = datetime_helpers.DatetimeWithNanoseconds.from_rfc3339(rfc3339_str)
    
    # Check nanosecond preservation
    assert dt.nanosecond == dt_reconstructed.nanosecond, \
        f"Nanosecond precision should be preserved: {dt.nanosecond} != {dt_reconstructed.nanosecond}"
    
    # Check date/time components
    assert dt.year == dt_reconstructed.year
    assert dt.month == dt_reconstructed.month
    assert dt.day == dt_reconstructed.day
    assert dt.hour == dt_reconstructed.hour
    assert dt.minute == dt_reconstructed.minute
    assert dt.second == dt_reconstructed.second


# Test 5: protobuf_helpers.check_oneof property
@given(
    kwargs=st.dictionaries(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=10),
        st.one_of(st.none(), st.integers(), st.text()),
        min_size=0,
        max_size=5
    )
)
def test_protobuf_check_oneof(kwargs):
    """Test that check_oneof raises ValueError if more than one kwarg is not None."""
    non_none_count = sum(1 for v in kwargs.values() if v is not None)
    
    if non_none_count > 1:
        with pytest.raises(ValueError, match="Only one of .* should be set"):
            protobuf_helpers.check_oneof(**kwargs)
    else:
        # Should not raise
        protobuf_helpers.check_oneof(**kwargs)


# Test 6: protobuf_helpers._resolve_subkeys property
@given(
    key=st.text(min_size=1, max_size=50),
    separator=st.sampled_from(['.', '|', '/', '::'])
)
def test_resolve_subkeys_property(key, separator):
    """Test that _resolve_subkeys correctly splits keys."""
    result_key, result_subkey = protobuf_helpers._resolve_subkeys(key, separator)
    
    if separator in key:
        # Should split on first occurrence
        expected_parts = key.split(separator, 1)
        assert result_key == expected_parts[0]
        assert result_subkey == expected_parts[1]
        
        # Rejoining should give original
        reconstructed = result_key + separator + result_subkey
        assert reconstructed == key
    else:
        # No separator, subkey should be None
        assert result_key == key
        assert result_subkey is None


# Test 7: ISO8601 date parsing round-trip
@given(
    year=st.integers(min_value=1000, max_value=9999),  # Avoid years < 1000 due to strftime limitations
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28)
)
def test_iso8601_date_roundtrip(year, month, day):
    """Test that ISO8601 date string parsing is consistent."""
    date_str = f"{year:04d}-{month:02d}-{day:02d}"
    parsed_date = datetime_helpers.from_iso8601_date(date_str)
    
    assert parsed_date.year == year
    assert parsed_date.month == month
    assert parsed_date.day == day
    
    # Round-trip through string format
    reconstructed_str = parsed_date.strftime("%Y-%m-%d")
    assert reconstructed_str == date_str


# Test 8: ISO8601 time parsing
@given(
    hour=st.integers(min_value=0, max_value=23),
    minute=st.integers(min_value=0, max_value=59),
    second=st.integers(min_value=0, max_value=59)
)
def test_iso8601_time_parsing(hour, minute, second):
    """Test that ISO8601 time string parsing is consistent."""
    time_str = f"{hour:02d}:{minute:02d}:{second:02d}"
    parsed_time = datetime_helpers.from_iso8601_time(time_str)
    
    assert parsed_time.hour == hour
    assert parsed_time.minute == minute
    assert parsed_time.second == second


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])