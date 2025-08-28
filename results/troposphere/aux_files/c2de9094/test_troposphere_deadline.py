"""
Property-based tests for troposphere.deadline module
"""

import math
import sys
import traceback
from decimal import Decimal

import pytest
from hypothesis import assume, given, strategies as st, settings

# Add site-packages to path
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

import troposphere.deadline as deadline


# Test the double validator function
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text().filter(lambda x: x.strip() != ""),  # non-empty strings
    st.decimals(allow_nan=False, allow_infinity=False),
))
def test_double_validator_accepts_valid_inputs(x):
    """Test that double() accepts valid numeric inputs and returns them unchanged."""
    try:
        # For strings, check if they can be converted to float first
        if isinstance(x, str):
            try:
                float(x)
            except (ValueError, TypeError):
                # Skip strings that can't be converted to float
                assume(False)
        
        result = deadline.double(x)
        assert result is x  # Should return the exact same object
    except ValueError:
        # If it raises ValueError, ensure the input truly can't be converted to float
        if not isinstance(x, str):
            pytest.fail(f"double() rejected valid input: {x}")
        else:
            # For strings, ensure they really can't be converted
            with pytest.raises((ValueError, TypeError)):
                float(x)


@given(st.one_of(
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
    st.tuples(st.integers()),
))
def test_double_validator_rejects_invalid_types(x):
    """Test that double() rejects invalid input types."""
    with pytest.raises(ValueError) as exc_info:
        deadline.double(x)
    assert "is not a valid double" in str(exc_info.value)


# Test the integer validator function
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x == int(x)),
    st.text().filter(lambda x: x.strip() != ""),
    st.booleans(),
))
def test_integer_validator_accepts_valid_inputs(x):
    """Test that integer() accepts valid integer inputs and returns them unchanged."""
    try:
        # For strings, check if they can be converted to int first
        if isinstance(x, str):
            try:
                int(x)
            except (ValueError, TypeError):
                # Skip strings that can't be converted to int
                assume(False)
        
        result = deadline.integer(x)
        assert result is x  # Should return the exact same object
    except ValueError:
        # If it raises ValueError, ensure the input truly can't be converted to int
        if not isinstance(x, str):
            pytest.fail(f"integer() rejected valid input: {x}")
        else:
            # For strings, ensure they really can't be converted
            with pytest.raises((ValueError, TypeError)):
                int(x)


@given(st.one_of(
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
    st.tuples(st.integers()),
))
def test_integer_validator_rejects_invalid_types(x):
    """Test that integer() rejects invalid input types."""
    with pytest.raises(ValueError) as exc_info:
        deadline.integer(x)
    assert "is not a valid integer" in str(exc_info.value)


# Test Range classes with Min/Max properties
@given(
    min_val=st.integers(min_value=-1000000, max_value=1000000),
    max_val=st.integers(min_value=-1000000, max_value=1000000),
)
def test_accelerator_count_range_accepts_any_min_max(min_val, max_val):
    """Test that AcceleratorCountRange accepts any integer values for Min and Max."""
    # The class should accept any Min and Max values, even if Min > Max
    # This tests that the class itself doesn't validate the invariant
    range_obj = deadline.AcceleratorCountRange(Min=min_val, Max=max_val)
    
    # Verify the values are stored correctly
    assert range_obj.properties.get("Min") == min_val
    assert range_obj.properties.get("Max") == max_val
    
    # Convert to dict to ensure validation passes
    dict_repr = range_obj.to_dict()
    assert dict_repr["Min"] == min_val
    assert dict_repr.get("Max") == max_val


@given(
    min_val=st.integers(min_value=0, max_value=1000000),
    max_val=st.integers(min_value=0, max_value=1000000),
)
def test_memory_mib_range_accepts_any_min_max(min_val, max_val):
    """Test that MemoryMiBRange accepts any integer values for Min and Max."""
    range_obj = deadline.MemoryMiBRange(Min=min_val, Max=max_val)
    
    # Verify the values are stored correctly
    assert range_obj.properties.get("Min") == min_val
    assert range_obj.properties.get("Max") == max_val
    
    # Convert to dict to ensure validation passes
    dict_repr = range_obj.to_dict()
    assert dict_repr["Min"] == min_val
    assert dict_repr.get("Max") == max_val


@given(
    min_val=st.integers(min_value=1, max_value=1000),
    max_val=st.integers(min_value=1, max_value=1000),
)
def test_vcpu_count_range_accepts_any_min_max(min_val, max_val):
    """Test that VCpuCountRange accepts any integer values for Min and Max."""
    range_obj = deadline.VCpuCountRange(Min=min_val, Max=max_val)
    
    # Verify the values are stored correctly
    assert range_obj.properties.get("Min") == min_val
    assert range_obj.properties.get("Max") == max_val
    
    # Convert to dict to ensure validation passes
    dict_repr = range_obj.to_dict()
    assert dict_repr["Min"] == min_val
    assert dict_repr.get("Max") == max_val


# Test that range classes use the integer validator
@given(st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x != int(x)))
def test_range_classes_reject_non_integers(float_val):
    """Test that Range classes reject non-integer values through the integer validator."""
    # AcceleratorCountRange should reject non-integers
    with pytest.raises(TypeError) as exc_info:
        deadline.AcceleratorCountRange(Min=float_val)
    assert "Min" in str(exc_info.value)
    
    # MemoryMiBRange should reject non-integers  
    with pytest.raises(TypeError) as exc_info:
        deadline.MemoryMiBRange(Min=float_val)
    assert "Min" in str(exc_info.value)
    
    # VCpuCountRange should reject non-integers
    with pytest.raises(TypeError) as exc_info:
        deadline.VCpuCountRange(Min=float_val)
    assert "Min" in str(exc_info.value)


# Test string inputs that look like numbers
@given(st.text(min_size=1).filter(lambda x: x.strip() and not x.strip().lstrip('-').isdigit()))
def test_integer_validator_string_handling(s):
    """Test that integer validator properly handles string inputs."""
    # Strings that can't be converted to int should raise ValueError
    try:
        int(s)
        can_convert = True
    except (ValueError, TypeError):
        can_convert = False
    
    if can_convert:
        result = deadline.integer(s)
        assert result is s  # Should return the same string object
    else:
        with pytest.raises(ValueError) as exc_info:
            deadline.integer(s)
        assert "is not a valid integer" in str(exc_info.value)


@given(st.text(min_size=1).filter(lambda x: x.strip()))
def test_double_validator_string_handling(s):
    """Test that double validator properly handles string inputs."""
    # Strings that can't be converted to float should raise ValueError
    try:
        float(s)
        can_convert = True
    except (ValueError, TypeError):
        can_convert = False
    
    if can_convert:
        result = deadline.double(s)
        assert result is s  # Should return the same string object
    else:
        with pytest.raises(ValueError) as exc_info:
            deadline.double(s)
        assert "is not a valid double" in str(exc_info.value)


# Test edge cases with special numeric strings
@given(st.sampled_from(["inf", "-inf", "nan", "NaN", "Infinity", "-Infinity"]))
def test_double_validator_special_float_strings(s):
    """Test that double validator handles special float string representations."""
    result = deadline.double(s)
    assert result is s  # These should be accepted as they convert to float
    # Verify they actually convert to special float values
    float_val = float(s)
    assert math.isinf(float_val) or math.isnan(float_val)


@given(st.sampled_from(["inf", "-inf", "nan", "NaN", "Infinity", "-Infinity"]))
def test_integer_validator_special_float_strings(s):
    """Test that integer validator rejects special float string representations."""
    with pytest.raises(ValueError) as exc_info:
        deadline.integer(s)
    assert "is not a valid integer" in str(exc_info.value)


# Test validation of FleetAmountCapability Min/Max 
@given(
    min_val=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    max_val=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
)
def test_fleet_amount_capability_accepts_any_min_max(min_val, max_val, name):
    """Test that FleetAmountCapability accepts any float values for Min and Max."""
    capability = deadline.FleetAmountCapability(Name=name, Min=min_val, Max=max_val)
    
    # Verify the values are stored correctly
    assert capability.properties.get("Name") == name
    assert capability.properties.get("Min") == min_val
    assert capability.properties.get("Max") == max_val
    
    # Convert to dict to ensure validation passes
    dict_repr = capability.to_dict()
    assert dict_repr["Name"] == name
    assert dict_repr["Min"] == min_val
    assert dict_repr.get("Max") == max_val


if __name__ == "__main__":
    # Run a quick smoke test
    print("Running smoke tests...")
    test_double_validator_accepts_valid_inputs()
    test_integer_validator_accepts_valid_inputs()
    print("Smoke tests passed!")