import math
import uuid as uuid_module
from datetime import datetime
from hypothesis import assume, given, strategies as st, settings, example
import click.types


@given(st.integers(min_value=-100, max_value=100),
       st.integers(min_value=-100, max_value=100))
def test_int_range_operator_bug(min_val, max_val):
    """Test that IntRange uses wrong comparison operators for open bounds"""
    assume(min_val < max_val)
    
    range_min_open = click.types.IntRange(min=min_val, max=max_val, min_open=True)
    range_max_open = click.types.IntRange(min=min_val, max=max_val, max_open=True)
    
    # Test boundary values
    if min_val < max_val:
        # Test that min_open uses wrong operator (should reject min_val but might not)
        try:
            result = range_min_open.convert(min_val, None, None)
            # If this succeeds, there's a bug - min_val should be rejected with min_open=True
            print(f"BUG: min_open=True accepted boundary value {min_val}")
        except click.types.BadParameter:
            pass
        
        # Test that max_open uses wrong operator (should reject max_val but might not)
        try:
            result = range_max_open.convert(max_val, None, None)
            # If this succeeds, there's a bug - max_val should be rejected with max_open=True
            print(f"BUG: max_open=True accepted boundary value {max_val}")
        except click.types.BadParameter:
            pass


@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100),
       st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100))
def test_float_range_operator_bug(min_val, max_val):
    """Test that FloatRange uses wrong comparison operators for open bounds"""
    assume(min_val < max_val)
    assume(abs(max_val - min_val) > 0.01)
    
    range_min_open = click.types.FloatRange(min=min_val, max=max_val, min_open=True)
    range_max_open = click.types.FloatRange(min=min_val, max=max_val, max_open=True)
    
    # Test boundary values - the code in lines 522-527 appears to have inverted operators
    try:
        result = range_min_open.convert(min_val, None, None)
        print(f"BUG: min_open=True accepted boundary value {min_val}")
    except click.types.BadParameter:
        pass
        
    try:
        result = range_max_open.convert(max_val, None, None)
        print(f"BUG: max_open=True accepted boundary value {max_val}")
    except click.types.BadParameter:
        pass


# Let me check the actual implementation
@given(st.integers())
def test_range_open_bounds_logic_error(value):
    """Test the operator logic in _NumberRangeBase.convert"""
    # Looking at lines 522-527, the operators appear inverted:
    # lt_min uses (operator.le if self.min_open else operator.lt)
    # But if min_open is True, we want to exclude the boundary, so should use lt, not le
    
    int_range = click.types.IntRange(min=10, max=20, min_open=True, max_open=True)
    
    # Value exactly at min boundary (10)
    if value == 10:
        try:
            result = int_range.convert(value, None, None)
            # This should fail but might not due to operator inversion
            assert False, f"BUG FOUND: min_open=True accepted boundary value {value}"
        except click.types.BadParameter:
            pass
    
    # Value exactly at max boundary (20)
    if value == 20:
        try:
            result = int_range.convert(value, None, None)
            # This should fail but might not due to operator inversion
            assert False, f"BUG FOUND: max_open=True accepted boundary value {value}"
        except click.types.BadParameter:
            pass
    
    # Values inside should work
    if 10 < value < 20:
        result = int_range.convert(value, None, None)
        assert result == value


# Direct test to confirm the bug
def test_open_bounds_operator_bug_direct():
    """Direct test showing the operator inversion bug"""
    
    # Test with IntRange
    int_range = click.types.IntRange(min=10, max=20, min_open=True, max_open=True)
    
    # These should fail but won't due to the bug
    try:
        result = int_range.convert(10, None, None)
        print(f"IntRange BUG: min_open=True incorrectly accepted min boundary value 10, got {result}")
        assert False, "Bug found: min boundary accepted with min_open=True"
    except click.types.BadParameter:
        print("IntRange correctly rejected min boundary with min_open=True")
    
    try:
        result = int_range.convert(20, None, None)
        print(f"IntRange BUG: max_open=True incorrectly accepted max boundary value 20, got {result}")
        assert False, "Bug found: max boundary accepted with max_open=True"
    except click.types.BadParameter:
        print("IntRange correctly rejected max boundary with max_open=True")
    
    # Test with FloatRange
    float_range = click.types.FloatRange(min=10.0, max=20.0, min_open=True, max_open=True)
    
    try:
        result = float_range.convert(10.0, None, None)
        print(f"FloatRange BUG: min_open=True incorrectly accepted min boundary value 10.0, got {result}")
        assert False, "Bug found: min boundary accepted with min_open=True"
    except click.types.BadParameter:
        print("FloatRange correctly rejected min boundary with min_open=True")
    
    try:
        result = float_range.convert(20.0, None, None)
        print(f"FloatRange BUG: max_open=True incorrectly accepted max boundary value 20.0, got {result}")
        assert False, "Bug found: max boundary accepted with max_open=True"
    except click.types.BadParameter:
        print("FloatRange correctly rejected max boundary with max_open=True")


if __name__ == "__main__":
    test_open_bounds_operator_bug_direct()