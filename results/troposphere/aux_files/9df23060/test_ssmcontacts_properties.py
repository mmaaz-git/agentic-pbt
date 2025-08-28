"""Property-based tests for troposphere.ssmcontacts module."""

import math
from hypothesis import given, strategies as st, assume, settings
import troposphere.ssmcontacts as ssmcontacts


# Property 1: integer function should convert to integer (based on name and validation logic)
# but actually returns the original value unchanged
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_integer_function_preserves_float_type(x):
    """The integer() function validates but doesn't convert floats to integers.
    
    This appears to be a bug: a function named 'integer' that validates
    int(x) works but returns the original float value unchanged.
    """
    assume(not math.isnan(x))
    
    # The function should logically return an integer
    result = ssmcontacts.integer(x)
    
    # Bug: The result preserves the original type instead of converting to int
    assert result == x  # This passes but shouldn't for a function named 'integer'
    assert type(result) == type(x)  # Float stays float
    
    # What we'd expect from a function named 'integer':
    # assert isinstance(result, int) or (isinstance(result, float) and result.is_integer())


# Property 2: boolean function should handle case-insensitive strings
@given(st.text())
def test_boolean_case_sensitivity(s):
    """The boolean() function is case-sensitive when it probably shouldn't be."""
    
    # Test TRUE/FALSE variations
    if s.lower() == 'true':
        if s in ['true', 'True']:
            # These work
            assert ssmcontacts.boolean(s) == True
        elif s in ['TRUE', 'tRue', 'TrUe']:
            # These should work but raise ValueError
            try:
                result = ssmcontacts.boolean(s)
                assert False, f"Expected ValueError for {s}, got {result}"
            except ValueError:
                pass  # Bug: case variations aren't handled
    
    if s.lower() == 'false':
        if s in ['false', 'False']:
            # These work
            assert ssmcontacts.boolean(s) == False
        elif s in ['FALSE', 'fAlse', 'FaLsE']:
            # These should work but raise ValueError
            try:
                result = ssmcontacts.boolean(s)
                assert False, f"Expected ValueError for {s}, got {result}"
            except ValueError:
                pass  # Bug: case variations aren't handled


# Property 3: Round-trip property for AWS objects
@given(
    start_time=st.text(min_size=1, max_size=10),
    end_time=st.text(min_size=1, max_size=10)
)
def test_coverage_time_round_trip(start_time, end_time):
    """to_dict and from_dict should be inverses for valid objects."""
    
    # Create object
    original = ssmcontacts.CoverageTime(StartTime=start_time, EndTime=end_time)
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Convert back from dict
    restored = ssmcontacts.CoverageTime.from_dict('test', dict_repr)
    
    # Should be equivalent
    assert restored.to_dict() == dict_repr
    assert restored.properties['StartTime'] == start_time
    assert restored.properties['EndTime'] == end_time


# Property 4: Integer field validation should reject or convert floats consistently
@given(st.floats(min_value=0, max_value=1000, exclude_min=False, exclude_max=False))
def test_duration_field_handles_floats(duration):
    """Integer fields should either reject floats or convert them to integers."""
    
    stage = ssmcontacts.Stage(DurationInMinutes=duration)
    
    # Get the validated value
    stage_dict = stage.to_dict()
    
    # Bug: Float values pass through unchanged in integer fields
    assert stage_dict['DurationInMinutes'] == duration
    
    # What we'd expect: either rejection or conversion
    # Either this should raise an error during validation for non-integers
    # Or it should convert to int(duration)


# Property 5: Required field validation
@given(st.text(min_size=1, max_size=10))
def test_required_field_validation(value):
    """Required fields should be enforced during validation."""
    
    # Create object missing required field
    ct = ssmcontacts.CoverageTime(StartTime=value)  # Missing EndTime
    
    # to_dict without validation works (bug?)
    dict_no_validation = ct.to_dict(validation=False)
    assert 'StartTime' in dict_no_validation
    assert 'EndTime' not in dict_no_validation
    
    # to_dict with validation should fail
    try:
        dict_with_validation = ct.to_dict(validation=True)
        assert False, "Expected validation error for missing required field"
    except ValueError as e:
        assert 'EndTime' in str(e)
        assert 'required' in str(e).lower()


# Property 6: Test MonthlySetting DayOfMonth validation
@given(st.integers())
def test_monthly_setting_day_validation(day):
    """DayOfMonth should validate as a reasonable day value."""
    
    try:
        ms = ssmcontacts.MonthlySetting(
            DayOfMonth=day,
            HandOffTime="12:00"
        )
        # If it accepts the value, it should preserve it
        assert ms.to_dict()['DayOfMonth'] == day
        
        # Note: Currently accepts any integer, including negative and > 31
        # This might be a validation bug
    except (ValueError, TypeError):
        # If it rejects, it should be for invalid days
        assert day < 1 or day > 31