#!/usr/bin/env python3
"""Property-based tests for troposphere.rbin module"""

import math
from hypothesis import given, assume, strategies as st, settings
import troposphere.rbin as rbin


# Test 1: integer() function type preservation property
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=1),
    st.booleans(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
    st.tuples(st.integers()),
    st.none()
))
def test_integer_type_preservation(x):
    """integer(x) should return x unchanged when it succeeds"""
    try:
        result = rbin.integer(x)
        # The function should return the exact same object
        assert result is x, f"integer() modified the input: {x} -> {result}"
    except ValueError:
        # If it raises ValueError, that's fine - we're testing when it succeeds
        pass


# Test 2: integer() validation consistency with int()
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.booleans(),
    st.lists(st.integers()),
    st.none()
))
def test_integer_validation_consistency(x):
    """If int(x) succeeds, integer(x) should succeed and vice versa"""
    int_succeeded = False
    integer_succeeded = False
    
    try:
        int(x)
        int_succeeded = True
    except (ValueError, TypeError):
        pass
    
    try:
        rbin.integer(x)
        integer_succeeded = True
    except ValueError:
        pass
    
    assert int_succeeded == integer_succeeded, \
        f"Validation inconsistency for {repr(x)}: int() {'succeeded' if int_succeeded else 'failed'}, integer() {'succeeded' if integer_succeeded else 'failed'}"


# Test 3: Round-trip property for valid integer inputs
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    st.text().filter(lambda s: s.strip() and (s.strip().isdigit() or (s.strip()[0] == '-' and s.strip()[1:].isdigit()))),
    st.booleans()
))
def test_integer_round_trip(x):
    """For valid inputs, int(integer(x)) should equal int(x)"""
    try:
        result = rbin.integer(x)
        # If integer() succeeds, converting both to int should give same value
        assert int(result) == int(x), f"Round-trip failed: int({x}) = {int(x)}, but int(integer({x})) = int({result}) = {int(result)}"
    except ValueError:
        # integer() can raise ValueError for invalid inputs
        pass
    except (TypeError, ValueError) as e:
        # int() conversion might fail even after integer() succeeds
        # This would be a bug!
        raise AssertionError(f"integer({x}) succeeded returning {rbin.integer(x)}, but int() conversion failed: {e}")


# Test 4: RetentionPeriod value validation using integer function
@given(
    st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.lists(st.integers()),
        st.none()
    ),
    st.text()
)
def test_retention_period_value_validation(value, unit):
    """RetentionPeriodValue should be validated by integer() function"""
    # First check if integer() would accept this value
    integer_accepts = False
    try:
        rbin.integer(value)
        integer_accepts = True
    except ValueError:
        pass
    
    # Now check if RetentionPeriod accepts it
    retention_accepts = False
    try:
        period = rbin.RetentionPeriod(RetentionPeriodValue=value, RetentionPeriodUnit=unit)
        retention_accepts = True
    except (ValueError, TypeError):
        pass
    
    # They should have the same behavior
    assert integer_accepts == retention_accepts, \
        f"Validation inconsistency: integer({repr(value)}) {'accepts' if integer_accepts else 'rejects'}, but RetentionPeriod {'accepts' if retention_accepts else 'rejects'}"


# Test 5: Tags round-trip property
@given(st.dictionaries(
    st.text(min_size=1, max_size=50).filter(lambda s: not s.startswith('_')),
    st.text(min_size=0, max_size=100),
    min_size=0,
    max_size=10
))
def test_tags_round_trip(tag_dict):
    """Tags should preserve data in dict -> Tags -> to_dict round trip"""
    tags = rbin.Tags(tag_dict)
    result = tags.to_dict()
    
    # Convert result back to dict format for comparison
    result_dict = {}
    for item in result:
        if isinstance(item, dict) and 'Key' in item and 'Value' in item:
            result_dict[item['Key']] = item['Value']
    
    assert result_dict == tag_dict, f"Round-trip failed: {tag_dict} -> {result} -> {result_dict}"


# Test 6: UnlockDelay value validation
@given(
    st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.none()
    )
)
def test_unlock_delay_value_validation(value):
    """UnlockDelayValue should be validated by integer() function"""
    integer_accepts = False
    try:
        rbin.integer(value)
        integer_accepts = True
    except ValueError:
        pass
    
    unlock_accepts = False
    try:
        # UnlockDelayUnit is optional, so we can omit it
        delay = rbin.UnlockDelay(UnlockDelayValue=value)
        unlock_accepts = True
    except (ValueError, TypeError):
        pass
    
    assert integer_accepts == unlock_accepts, \
        f"Validation inconsistency: integer({repr(value)}) {'accepts' if integer_accepts else 'rejects'}, but UnlockDelay {'accepts' if unlock_accepts else 'rejects'}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])