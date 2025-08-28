#!/usr/bin/env python3
"""Testing for potential bugs in troposphere.customerprofiles."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.customerprofiles as cp
from troposphere import validators
import pytest
import math


# Bug hunt 1: Boolean validator accepts strings that look like booleans
@given(st.text())
@settings(max_examples=1000)
def test_boolean_validator_string_bugs(text):
    """Hunt for strings that might be incorrectly accepted as booleans."""
    try:
        result = validators.boolean(text)
        # If it succeeds, it should be in the known mappings
        assert text in ["1", "0", "true", "True", "false", "False"]
    except ValueError:
        # Should fail for anything not in the mappings
        assert text not in ["1", "0", "true", "True", "false", "False"]


# Bug hunt 2: Integer validator with scientific notation strings
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_integer_validator_scientific_notation(value):
    """Test if integer validator handles scientific notation strings correctly."""
    sci_str = f"{value:e}"  # Convert to scientific notation string
    
    try:
        result = validators.integer(sci_str)
        # If it succeeds, int() should also succeed
        int_val = int(float(sci_str))
        # Result should be the original string
        assert result == sci_str
    except ValueError as e:
        # If it fails, it's because scientific notation isn't a valid integer format
        assert "not a valid integer" in str(e)
        # But float should succeed
        float(sci_str)


# Bug hunt 3: Double validator with special float values
def test_double_validator_special_floats():
    """Test double validator with special float values."""
    # Test infinity strings
    special_values = ["inf", "-inf", "infinity", "-infinity", "nan", "NaN"]
    
    for val in special_values:
        try:
            result = validators.double(val)
            # If it succeeds, float() should handle it
            float_val = float(val)
            assert result == val
            print(f"double({val}) = {result}, float({val}) = {float_val}")
        except ValueError as e:
            print(f"double({val}) failed: {e}")
            # If validator fails, float() should also fail
            with pytest.raises(ValueError):
                float(val)


# Bug hunt 4: Classes that accept lists - do they validate list items?
@given(st.lists(st.one_of(st.integers(), st.text(), st.none()), min_size=1, max_size=5))
def test_list_field_validation(values):
    """Test if list fields properly validate their items."""
    # MatchingRule has a Rule field that expects [str]
    try:
        rule = cp.MatchingRule(Rule=values)
        # If it succeeds, all values should be strings (or convertible)
        result = rule.to_dict()
        assert 'Rule' in result
        # Check if non-strings were accepted
        for v in values:
            if v is None:
                # None should have failed
                assert False, f"MatchingRule accepted None in list"
    except (TypeError, ValueError) as e:
        # Should fail if list contains non-strings
        has_non_string = any(not isinstance(v, str) for v in values)
        assert has_non_string or None in values


# Bug hunt 5: Range validation - what if Value and ValueRange are both provided?
@given(
    st.integers(min_value=0, max_value=100),
    st.integers(min_value=0, max_value=100),
    st.integers(min_value=0, max_value=100)
)
def test_range_conflicting_values(value, start, end):
    """Test Range class when both Value and ValueRange are provided."""
    # The Range class has both Value and ValueRange as optional
    # What happens if both are provided?
    vr = cp.ValueRange(Start=start, End=end)
    range_obj = cp.Range(
        Unit="days",
        Value=value,
        ValueRange=vr
    )
    
    result = range_obj.to_dict()
    # Both should be in the result
    assert result['Unit'] == 'days'
    assert 'Value' in result
    assert 'ValueRange' in result
    # This might be a logical issue - having both single value and range


# Bug hunt 6: Test if validators preserve type or convert
@given(st.sampled_from(["123", 123, True, 1.0]))
def test_validator_type_preservation(value):
    """Test if validators preserve the original type or convert."""
    # Integer validator
    try:
        int_result = validators.integer(value)
        assert int_result == value  # Should preserve original
        assert type(int_result) == type(value)  # Should preserve type
    except ValueError:
        pass
    
    # Double validator
    try:
        double_result = validators.double(value)
        assert double_result == value  # Should preserve original
        assert type(double_result) == type(value)  # Should preserve type
    except ValueError:
        pass


# Bug hunt 7: Test AWSProperty vs AWSObject title requirements
def test_title_requirement_inconsistency():
    """Test if AWSProperty and AWSObject have different title requirements."""
    # AWSProperty classes shouldn't require title
    prop = cp.AttributeItem(Name="test")
    assert prop.to_dict() == {'Name': 'test'}
    
    # But AWSObject classes do require title
    try:
        obj = cp.Domain(DomainName="test", DefaultExpirationDays=30)
        assert False, "Domain should require title parameter"
    except TypeError as e:
        assert "missing 1 required positional argument: 'title'" in str(e)
    
    # With title it should work
    obj = cp.Domain("MyDomain", DomainName="test", DefaultExpirationDays=30)
    result = obj.to_dict()
    assert 'Type' in result
    assert result['Type'] == 'AWS::CustomerProfiles::Domain'


# Bug hunt 8: Test integer overflow behavior
@given(st.integers())
def test_integer_overflow_behavior(value):
    """Test how the library handles very large integers."""
    # Python has arbitrary precision integers, but JSON/AWS might not
    vr = cp.ValueRange(Start=value, End=value)
    result = vr.to_dict()
    
    # The values should be preserved exactly
    assert result['Start'] == value
    assert result['End'] == value
    
    # But what happens when serialized to JSON?
    import json
    json_str = json.dumps(result)
    parsed = json.loads(json_str)
    
    # For very large integers, JSON might lose precision
    if abs(value) > 2**53:  # JavaScript's Number.MAX_SAFE_INTEGER
        # This might not round-trip correctly
        pass
    else:
        assert parsed['Start'] == value
        assert parsed['End'] == value


if __name__ == "__main__":
    # Run specific tests that might find bugs
    print("Testing double validator with special floats:")
    test_double_validator_special_floats()
    
    print("\nTesting title requirement inconsistency:")
    test_title_requirement_inconsistency()
    
    print("\nRunning all tests with pytest...")
    pytest.main([__file__, "-v", "--tb=short", "-q"])