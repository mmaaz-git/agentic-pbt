#!/usr/bin/env python3
"""Edge case testing for troposphere.rbin module"""

import math
import sys
from decimal import Decimal
from hypothesis import given, strategies as st, settings, example
import troposphere.rbin as rbin


# Test with extreme values and edge cases
@given(st.one_of(
    st.floats(allow_nan=True, allow_infinity=True),  # Test with NaN and Inf
    st.decimals(allow_nan=True, allow_infinity=True),  # Decimal types
    st.complex_numbers(),  # Complex numbers
    st.fractions(),  # Fraction type
    st.binary(),  # Binary data
    st.text().map(lambda s: s.strip()),  # Empty strings
    st.just(object()),  # Generic objects
    st.just(lambda x: x),  # Functions
))
@settings(max_examples=500)
def test_integer_edge_cases(x):
    """Test integer() with extreme and unusual inputs"""
    try:
        result = rbin.integer(x)
        # If it succeeds, result should be x
        assert result is x
        # And int(x) should also work
        int_val = int(x)
    except ValueError:
        # Expected for invalid inputs
        pass
    except TypeError:
        # Also possible for some types
        pass


# Test numeric edge cases specifically
@given(st.one_of(
    st.just(float('inf')),
    st.just(float('-inf')),
    st.just(float('nan')),
    st.just(sys.maxsize),
    st.just(sys.maxsize + 1),
    st.just(-sys.maxsize - 1),
    st.just(0.999999999999999),
    st.just(1.0000000000000001),
    st.floats(min_value=1e308, max_value=1.7e308),  # Near float max
))
def test_integer_numeric_extremes(x):
    """Test integer() with numeric extremes"""
    int_error = None
    integer_error = None
    
    try:
        int_val = int(x)
    except (ValueError, TypeError, OverflowError) as e:
        int_error = type(e).__name__
    
    try:
        integer_val = rbin.integer(x)
    except ValueError as e:
        integer_error = "ValueError"
    
    # Check if both behave the same way
    if int_error is None and integer_error is None:
        # Both succeeded
        assert rbin.integer(x) is x
    elif int_error is not None and integer_error is not None:
        # Both failed - this is OK
        pass
    else:
        # One succeeded and one failed - potential bug!
        raise AssertionError(
            f"Inconsistent behavior for {x}: int() {'succeeded' if int_error is None else f'raised {int_error}'}, "
            f"integer() {'succeeded' if integer_error is None else f'raised {integer_error}'}"
        )


# Test string representations of numbers
@given(st.one_of(
    st.just(""),
    st.just(" "),
    st.just("  123  "),
    st.just("+123"),
    st.just("-0"),
    st.just("00123"),
    st.just("1e10"),
    st.just("1.0"),
    st.just("0x123"),
    st.just("0o777"),
    st.just("0b1010"),
    st.text(alphabet="0123456789", min_size=100, max_size=1000),  # Very long number strings
))
def test_integer_string_representations(s):
    """Test integer() with various string representations"""
    int_succeeded = False
    integer_succeeded = False
    
    try:
        int(s)
        int_succeeded = True
    except (ValueError, TypeError):
        pass
    
    try:
        rbin.integer(s)
        integer_succeeded = True
    except ValueError:
        pass
    
    assert int_succeeded == integer_succeeded, \
        f"String '{s}' handling inconsistent: int() {'succeeded' if int_succeeded else 'failed'}, integer() {'succeeded' if integer_succeeded else 'failed'}"


# Test class subclasses and special methods
class IntLike:
    def __init__(self, value):
        self.value = value
    def __int__(self):
        return self.value

class BadInt:
    def __int__(self):
        raise ValueError("Can't convert")

class FakeInt:
    def __int__(self):
        return "not an int"  # Returns wrong type

@given(st.integers())
def test_integer_with_custom_classes(val):
    """Test integer() with objects that have __int__ method"""
    obj = IntLike(val)
    
    # Check if int() accepts it
    assert int(obj) == val
    
    # Check if integer() accepts it and preserves the object
    result = rbin.integer(obj)
    assert result is obj  # Should return the same object
    

def test_integer_with_bad_int_method():
    """Test integer() with object that has failing __int__"""
    obj = BadInt()
    
    # int() should raise ValueError
    try:
        int(obj)
        assert False, "int() should have raised"
    except ValueError:
        pass
    
    # integer() should also raise ValueError
    try:
        rbin.integer(obj)
        assert False, "integer() should have raised"
    except ValueError:
        pass


def test_integer_with_fake_int_method():
    """Test integer() with object that has wrong __int__ return type"""
    obj = FakeInt()
    
    # int() behavior
    int_error = None
    try:
        int(obj)
    except (TypeError, ValueError) as e:
        int_error = type(e).__name__
    
    # integer() behavior
    integer_error = None
    try:
        rbin.integer(obj)
    except ValueError as e:
        integer_error = "ValueError"
    
    # They should both fail
    assert int_error is not None and integer_error is not None, \
        f"Both should fail for fake __int__: int() {int_error}, integer() {integer_error}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])