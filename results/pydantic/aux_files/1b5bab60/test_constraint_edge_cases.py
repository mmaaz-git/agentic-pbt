"""Test for potential bugs in constraint validation."""

from decimal import Decimal
from hypothesis import given, assume, strategies as st
from pydantic import BaseModel, Field, ValidationError
import math


# Test decimal_places > max_digits edge case
@given(
    max_digits=st.integers(min_value=1, max_value=5),
    decimal_places=st.integers(min_value=1, max_value=10)
)
def test_decimal_places_exceeds_max_digits(max_digits: int, decimal_places: int):
    """Test Field behavior when decimal_places > max_digits."""
    assume(decimal_places > max_digits)  # Only test problematic case
    
    class TestModel(BaseModel):
        value: Decimal = Field(max_digits=max_digits, decimal_places=decimal_places)
    
    # This configuration doesn't make mathematical sense
    # No decimal can have more decimal places than total digits
    # Test various values to see if any can satisfy these constraints
    test_values = [
        Decimal("0"),
        Decimal("0.0"),
        Decimal("0.1"),
        Decimal("0.01"),
        Decimal("1"),
        Decimal("0." + "0" * (decimal_places - 1) + "1"),
    ]
    
    any_accepted = False
    for val in test_values:
        try:
            instance = TestModel(value=val)
            any_accepted = True
            # If something is accepted with decimal_places > max_digits, that's suspicious
            # Check if the value actually satisfies the stated constraints
            val_str = str(val)
            if '.' in val_str:
                integer_part, decimal_part = val_str.split('.')
                total_digits = len(integer_part.lstrip('0-')) + len(decimal_part)
                actual_decimal_places = len(decimal_part)
                
                # The value shouldn't be accepted if it violates the constraints
                assert total_digits <= max_digits, f"Value {val} has {total_digits} digits but max_digits={max_digits}"
                assert actual_decimal_places <= decimal_places, f"Value {val} has {actual_decimal_places} decimal places but decimal_places={decimal_places}"
        except ValidationError:
            pass  # Expected for most values
    
    # With decimal_places > max_digits, it should be impossible to satisfy both constraints
    assert not any_accepted, f"Field with max_digits={max_digits}, decimal_places={decimal_places} accepted values"


# Test pattern constraint with special regex patterns
@given(
    pattern=st.sampled_from([
        r"^$",  # Empty string only
        r".",   # Any single character
        r".*",  # Any string
        r"\d+", # Digits only
        r"[a-z]+",  # Lowercase only
        r"^[^a-z]+$",  # No lowercase
    ]),
    test_string=st.text(min_size=0, max_size=20)
)
def test_pattern_constraint_consistency(pattern: str, test_string: str):
    """Test that pattern constraints work correctly."""
    import re
    
    class TestModel(BaseModel):
        value: str = Field(pattern=pattern)
    
    # Check if the string matches the pattern
    matches = bool(re.search(pattern, test_string))
    
    try:
        instance = TestModel(value=test_string)
        # If accepted, it should match the pattern
        assert matches, f"String '{test_string}' accepted but doesn't match pattern '{pattern}'"
        assert instance.value == test_string
    except ValidationError:
        # If rejected, it should not match the pattern
        assert not matches, f"String '{test_string}' rejected but matches pattern '{pattern}'"


# Test multiple_of with very small values
@given(
    multiple_of=st.floats(min_value=1e-10, max_value=1e-5, allow_nan=False, allow_infinity=False),
    multiplier=st.integers(min_value=-100, max_value=100)
)
def test_multiple_of_small_values(multiple_of: float, multiplier: int):
    """Test multiple_of constraint with very small values (precision issues)."""
    class TestModel(BaseModel):
        value: float = Field(multiple_of=multiple_of)
    
    # Exact multiple
    test_value = multiple_of * multiplier
    
    try:
        instance = TestModel(value=test_value)
        # Check the value wasn't modified
        assert math.isclose(instance.value, test_value, rel_tol=1e-9), f"Value was modified from {test_value} to {instance.value}"
    except ValidationError as e:
        # This might fail due to floating point precision
        # Check if it's really not a multiple
        remainder = abs(test_value % multiple_of)
        relative_error = remainder / multiple_of if multiple_of != 0 else 0
        
        # If the relative error is very small, this is a precision issue
        if relative_error < 1e-10:
            # This is likely a floating point precision issue, not a real validation error
            pass
        else:
            raise AssertionError(f"True multiple {test_value} of {multiple_of} was rejected") from e


# Test interaction between allow_inf_nan and other constraints
@given(
    allow_inf_nan=st.booleans(),
    has_bounds=st.booleans()
)
def test_allow_inf_nan_interaction(allow_inf_nan: bool, has_bounds: bool):
    """Test how allow_inf_nan interacts with other numeric constraints."""
    kwargs = {'allow_inf_nan': allow_inf_nan}
    if has_bounds:
        kwargs['ge'] = -1000.0
        kwargs['le'] = 1000.0
    
    class TestModel(BaseModel):
        value: float = Field(**kwargs)
    
    # Test special values
    special_values = [float('inf'), float('-inf'), float('nan')]
    
    for val in special_values:
        try:
            instance = TestModel(value=val)
            # If accepted, allow_inf_nan should be True
            assert allow_inf_nan, f"Special value {val} accepted with allow_inf_nan=False"
            # Also, if bounds are set, inf values shouldn't satisfy them
            if has_bounds and math.isinf(val):
                # Infinity can't be between -1000 and 1000
                assert False, f"Infinity value {val} accepted despite bounds"
        except ValidationError:
            # Expected when allow_inf_nan=False or when bounds exclude the value
            pass