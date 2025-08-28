"""Property-based tests for google.api_core using Hypothesis."""

import sys
import datetime
sys.path.insert(0, '/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
import math

# Import modules to test
from google.api_core import path_template
from google.api_core import datetime_helpers
from google.api_core import protobuf_helpers


# Strategy for generating valid path template variables
@st.composite
def path_template_vars(draw):
    """Generate valid path template and matching variables."""
    # Choose template pattern
    template_type = draw(st.sampled_from(['simple', 'named', 'complex']))
    
    if template_type == 'simple':
        # Simple positional template like 'users/*/messages/*'
        template = draw(st.sampled_from([
            'users/*/messages/*',
            'projects/*/locations/*',
            'shelves/*/books/*',
            'folders/*/files/*'
        ]))
        # Count the number of * in template
        num_vars = template.count('*')
        # Generate matching positional args
        args = draw(st.lists(
            st.text(alphabet=st.characters(blacklist_characters='/{}'), min_size=1, max_size=20),
            min_size=num_vars,
            max_size=num_vars
        ))
        return template, args, {}
    
    elif template_type == 'named':
        # Named variable template like '/v1/{name=shelves/*/books/*}'
        base_patterns = [
            ('shelves/*/books/*', 2),
            ('users/*/posts/*', 2),
            ('projects/*/regions/*', 2),
        ]
        pattern, num_stars = draw(st.sampled_from(base_patterns))
        var_name = draw(st.text(alphabet=st.characters(blacklist_characters='/{}='), min_size=1, max_size=10))
        template = f'/v1/{{{var_name}={pattern}}}'
        
        # Generate value matching the pattern
        parts = draw(st.lists(
            st.text(alphabet=st.characters(blacklist_characters='/{}'), min_size=1, max_size=20),
            min_size=num_stars,
            max_size=num_stars
        ))
        # Build the value string
        value = pattern
        for part in parts:
            value = value.replace('*', part, 1)
        
        return template, [], {var_name: value}
    
    else:  # complex
        # Mix of positional and named
        var_name = draw(st.text(alphabet=st.characters(blacklist_characters='/{}='), min_size=1, max_size=10))
        template = f'users/*/messages/{{{var_name}}}'
        pos_arg = draw(st.text(alphabet=st.characters(blacklist_characters='/{}'), min_size=1, max_size=20))
        named_arg = draw(st.text(alphabet=st.characters(blacklist_characters='/{}'), min_size=1, max_size=20))
        return template, [pos_arg], {var_name: named_arg}


@given(path_template_vars())
def test_path_template_expand_validate_round_trip(template_and_vars):
    """Test that expand and validate form a round-trip."""
    template, args, kwargs = template_and_vars
    
    # Expand the template
    try:
        expanded = path_template.expand(template, *args, **kwargs)
    except ValueError:
        # If expansion fails, it should be due to missing variables
        # This is expected behavior, not a bug
        return
    
    # The expanded path should validate against the original template
    assert path_template.validate(template, expanded), \
        f"Expanded path '{expanded}' does not validate against template '{template}'"


@given(
    st.datetimes(
        min_value=datetime.datetime(1970, 1, 2, tzinfo=datetime.timezone.utc),
        max_value=datetime.datetime(2100, 1, 1, tzinfo=datetime.timezone.utc)
    )
)
def test_datetime_microseconds_round_trip(dt):
    """Test that to_microseconds and from_microseconds form a round-trip."""
    # Ensure datetime is timezone-aware
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    
    # Convert to microseconds and back
    micros = datetime_helpers.to_microseconds(dt)
    result = datetime_helpers.from_microseconds(micros)
    
    # The result should match the original (considering microsecond precision)
    # Need to normalize to UTC for comparison
    dt_utc = dt.astimezone(datetime.timezone.utc)
    
    # Compare with microsecond precision
    assert result.year == dt_utc.year
    assert result.month == dt_utc.month
    assert result.day == dt_utc.day
    assert result.hour == dt_utc.hour
    assert result.minute == dt_utc.minute
    assert result.second == dt_utc.second
    assert result.microsecond == dt_utc.microsecond


@given(
    st.datetimes(
        min_value=datetime.datetime(1970, 1, 2),
        max_value=datetime.datetime(2100, 1, 1)
    )
)
def test_datetime_rfc3339_round_trip(dt):
    """Test that to_rfc3339 and from_rfc3339 form a round-trip."""
    # to_rfc3339 expects naive datetime and treats it as UTC
    if dt.tzinfo:
        dt = dt.replace(tzinfo=None)
    
    # Convert to RFC3339 string and back
    rfc3339_str = datetime_helpers.to_rfc3339(dt)
    result = datetime_helpers.from_rfc3339(rfc3339_str)
    
    # The result should be in UTC
    assert result.tzinfo == datetime.timezone.utc
    
    # Compare the values (result is UTC, original was naive/UTC)
    dt_utc = dt.replace(tzinfo=datetime.timezone.utc)
    
    assert result.year == dt_utc.year
    assert result.month == dt_utc.month
    assert result.day == dt_utc.day
    assert result.hour == dt_utc.hour
    assert result.minute == dt_utc.minute
    assert result.second == dt_utc.second
    assert result.microsecond == dt_utc.microsecond


@given(
    year=st.integers(min_value=1970, max_value=2100),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),  # Safe for all months
    hour=st.integers(min_value=0, max_value=23),
    minute=st.integers(min_value=0, max_value=59),
    second=st.integers(min_value=0, max_value=59),
    nanosecond=st.integers(min_value=0, max_value=999999999)
)
def test_datetime_with_nanoseconds_rfc3339_round_trip(year, month, day, hour, minute, second, nanosecond):
    """Test DatetimeWithNanoseconds RFC3339 round-trip."""
    # Create DatetimeWithNanoseconds
    dt = datetime_helpers.DatetimeWithNanoseconds(
        year, month, day, hour, minute, second,
        nanosecond=nanosecond,
        tzinfo=datetime.timezone.utc
    )
    
    # Convert to RFC3339 and back
    rfc3339_str = dt.rfc3339()
    result = datetime_helpers.DatetimeWithNanoseconds.from_rfc3339(rfc3339_str)
    
    # Check all fields match
    assert result.year == dt.year
    assert result.month == dt.month
    assert result.day == dt.day
    assert result.hour == dt.hour
    assert result.minute == dt.minute
    assert result.second == dt.second
    assert result.nanosecond == dt.nanosecond
    assert result.tzinfo == dt.tzinfo


@given(
    year=st.integers(min_value=1970, max_value=2100),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),  # Safe for all months
    hour=st.integers(min_value=0, max_value=23),
    minute=st.integers(min_value=0, max_value=59),
    second=st.integers(min_value=0, max_value=59),
    nanosecond=st.integers(min_value=0, max_value=999999999)
)
def test_datetime_with_nanoseconds_timestamp_pb_round_trip(year, month, day, hour, minute, second, nanosecond):
    """Test DatetimeWithNanoseconds timestamp_pb round-trip."""
    # Create DatetimeWithNanoseconds
    dt = datetime_helpers.DatetimeWithNanoseconds(
        year, month, day, hour, minute, second,
        nanosecond=nanosecond,
        tzinfo=datetime.timezone.utc
    )
    
    # Convert to timestamp_pb and back
    timestamp = dt.timestamp_pb()
    result = datetime_helpers.DatetimeWithNanoseconds.from_timestamp_pb(timestamp)
    
    # Check all fields match
    assert result.year == dt.year
    assert result.month == dt.month
    assert result.day == dt.day
    assert result.hour == dt.hour
    assert result.minute == dt.minute
    assert result.second == dt.second
    assert result.nanosecond == dt.nanosecond
    assert result.tzinfo == dt.tzinfo


@given(st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.one_of(st.none(), st.integers(), st.text()),
    min_size=0,
    max_size=5
))
def test_protobuf_check_oneof(kwargs):
    """Test check_oneof raises ValueError for multiple non-None values."""
    non_none_count = sum(1 for v in kwargs.values() if v is not None)
    
    if non_none_count > 1:
        # Should raise ValueError
        with pytest.raises(ValueError, match="Only one of .* should be set"):
            protobuf_helpers.check_oneof(**kwargs)
    else:
        # Should not raise
        protobuf_helpers.check_oneof(**kwargs)


@given(
    key=st.text(min_size=1, max_size=20),
    separator=st.sampled_from(['.', '|', '/', '-', '_'])
)
def test_protobuf_resolve_subkeys(key, separator):
    """Test _resolve_subkeys splits correctly on first separator."""
    result_key, result_subkey = protobuf_helpers._resolve_subkeys(key, separator)
    
    if separator in key:
        # Should split on first occurrence
        expected_parts = key.split(separator, 1)
        assert result_key == expected_parts[0]
        assert result_subkey == expected_parts[1]
        # Reconstruct should give original
        assert result_key + separator + result_subkey == key
    else:
        # No separator, subkey should be None
        assert result_key == key
        assert result_subkey is None


# Additional test for path_template edge cases
@given(st.text(min_size=0, max_size=100))
def test_path_template_validate_with_literals(template):
    """Test that templates without variables validate exact matches."""
    # Skip if template contains variable markers
    assume('*' not in template and '{' not in template and '}' not in template)
    
    # A template without variables should validate itself
    assert path_template.validate(template, template)
    
    # And should not validate anything different
    if template:
        assert not path_template.validate(template, template + 'x')


if __name__ == "__main__":
    # Run with increased examples for better coverage
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))