"""Deeper property-based tests for fire.test_components module."""

import math
from hypothesis import given, strategies as st, assume, settings
import fire.test_components as tc


# Test 10: WithDefaults.double should double the input as documented
@given(st.integers(min_value=-10**6, max_value=10**6))
def test_with_defaults_double(count):
    """Test that WithDefaults.double returns count * 2 as documented."""
    obj = tc.WithDefaults()
    result = obj.double(count)
    expected = 2 * count
    assert result == expected, f"double({count}) should return {expected}, got {result}"


# Test 11: WithDefaults.triple should triple the input
@given(st.integers(min_value=-10**6, max_value=10**6))
def test_with_defaults_triple(count):
    """Test that WithDefaults.triple returns count * 3."""
    obj = tc.WithDefaults()
    result = obj.triple(count)
    expected = 3 * count
    assert result == expected, f"triple({count}) should return {expected}, got {result}"


# Test 12: NamedTuplePoint should work correctly with different values
@given(
    st.floats(allow_nan=False, allow_infinity=False),
    st.floats(allow_nan=False, allow_infinity=False)
)
def test_named_tuple_point(x, y):
    """Test that NamedTuplePoint correctly stores x and y values."""
    point = tc.NamedTuplePoint(x, y)
    assert point.x == x, f"point.x should be {x}, got {point.x}"
    assert point.y == y, f"point.y should be {y}, got {point.y}"
    # Test tuple interface
    assert point[0] == x, f"point[0] should be {x}, got {point[0]}"
    assert point[1] == y, f"point[1] should be {y}, got {point[1]}"


# Test 13: Color enum should have correct values
def test_color_enum_values():
    """Test that Color enum has correct values."""
    assert tc.Color.RED.value == 1
    assert tc.Color.GREEN.value == 2
    assert tc.Color.BLUE.value == 3


# Test 14: InvalidProperty.double should work despite the invalid property
@given(st.integers(min_value=-10**6, max_value=10**6))
def test_invalid_property_double(number):
    """Test that InvalidProperty.double still works correctly."""
    obj = tc.InvalidProperty()
    result = obj.double(number)
    expected = 2 * number
    assert result == expected, f"double({number}) should return {expected}, got {result}"


# Test 15: BinaryCanvas negative sizes should be handled
@given(st.integers(min_value=-100, max_value=0))
def test_binary_canvas_negative_size(size):
    """Test BinaryCanvas behavior with negative or zero sizes."""
    if size <= 0:
        # Should either raise an error or handle gracefully
        try:
            canvas = tc.BinaryCanvas(size)
            # If it doesn't raise, check that it created something reasonable
            # This might reveal a bug if negative sizes are accepted
            assert isinstance(canvas.pixels, list)
        except (ValueError, IndexError, TypeError) as e:
            # Expected behavior - negative size should raise an error
            pass


# Test 16: Test OrderedDictionary methods
def test_ordered_dictionary_methods():
    """Test OrderedDictionary empty and non_empty methods."""
    od = tc.OrderedDictionary()
    
    # Test empty method
    empty_result = od.empty()
    assert isinstance(empty_result, dict), f"empty() should return dict, got {type(empty_result)}"
    assert len(empty_result) == 0, f"empty() should return empty dict, got {empty_result}"
    
    # Test non_empty method  
    non_empty_result = od.non_empty()
    assert isinstance(non_empty_result, dict), f"non_empty() should return dict, got {type(non_empty_result)}"
    assert len(non_empty_result) > 0, f"non_empty() should return non-empty dict"


# Test 17: Test decorated_method function
@given(st.integers())
def test_decorated_method(value):
    """Test decorated_method function."""
    # First check what decorated_method does
    result = tc.decorated_method(value)
    # Should verify what the decorator does
    assert result is not None


# Test 18: BinaryCanvas with size=0 edge case
def test_binary_canvas_zero_size():
    """Test BinaryCanvas with size=0 - potential edge case."""
    try:
        canvas = tc.BinaryCanvas(0)
        # If it doesn't raise, check behavior
        canvas.move(0, 0)  # This might cause division by zero in modulo
        canvas.on()
    except (ValueError, ZeroDivisionError, IndexError) as e:
        # Expected - size 0 should cause issues
        pass


# Test 19: Test type annotations in TypedProperties
def test_typed_properties():
    """Test TypedProperties class."""
    tp = tc.TypedProperties()
    # Check if it has expected attributes based on introspection
    attrs = dir(tp)
    # Just verify it can be instantiated
    assert tp is not None