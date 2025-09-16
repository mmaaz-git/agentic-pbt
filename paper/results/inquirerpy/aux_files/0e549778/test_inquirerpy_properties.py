"""Property-based tests for InquirerPy.inquirer using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from decimal import Decimal
from hypothesis import given, strategies as st, assume, settings
import pytest
from InquirerPy.prompts.number import NumberPrompt
from InquirerPy.prompts.input import InputPrompt
from InquirerPy.exceptions import InvalidArgument


# Test 1: NumberPrompt min/max constraints
@given(
    min_val=st.integers(min_value=-1000, max_value=1000),
    max_val=st.integers(min_value=-1000, max_value=1000),
    test_val=st.integers(min_value=-10000, max_value=10000)
)
def test_number_prompt_min_max_constraints(min_val, max_val, test_val):
    """Values should be clamped to min_allowed/max_allowed bounds."""
    assume(min_val <= max_val)
    
    prompt = NumberPrompt(
        message="Test",
        min_allowed=min_val,
        max_allowed=max_val,
        default=min_val  # Start with valid default
    )
    
    # Set value directly through the property
    prompt.value = test_val
    
    # Value should be clamped
    assert prompt.value >= min_val
    assert prompt.value <= max_val
    
    if test_val < min_val:
        assert prompt.value == min_val
    elif test_val > max_val:
        assert prompt.value == max_val
    else:
        assert prompt.value == test_val


# Test 2: NumberPrompt float handling with min/max
@given(
    min_val=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    max_val=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    test_val=st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
)
def test_number_prompt_float_min_max_constraints(min_val, max_val, test_val):
    """Float values should be clamped to min_allowed/max_allowed bounds."""
    assume(min_val <= max_val)
    
    prompt = NumberPrompt(
        message="Test",
        float_allowed=True,
        min_allowed=min_val,
        max_allowed=max_val,
        default=min_val  # Start with valid default
    )
    
    # Set value directly
    prompt.value = Decimal(str(test_val))
    
    # Value should be clamped (as Decimal)
    assert prompt.value >= Decimal(str(min_val))
    assert prompt.value <= Decimal(str(max_val))


# Test 3: NumberPrompt default type validation
@given(
    float_allowed=st.booleans(),
    default_int=st.integers(min_value=-1000, max_value=1000),
    default_float=st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
)
def test_number_prompt_default_type_validation(float_allowed, default_int, default_float):
    """Default values must match float_allowed setting."""
    
    if float_allowed:
        # Should accept float defaults when float_allowed=True
        prompt = NumberPrompt(
            message="Test",
            float_allowed=True,
            default=default_float
        )
        assert isinstance(prompt._default, Decimal)
        
        # Should also accept int defaults (converted to Decimal)
        prompt2 = NumberPrompt(
            message="Test", 
            float_allowed=True,
            default=default_int
        )
        assert isinstance(prompt2._default, Decimal)
    else:
        # Should accept int defaults when float_allowed=False
        prompt = NumberPrompt(
            message="Test",
            float_allowed=False,
            default=default_int
        )
        assert prompt._default == default_int
        
        # Should raise error for float defaults when float_allowed=False
        with pytest.raises(InvalidArgument):
            NumberPrompt(
                message="Test",
                float_allowed=False, 
                default=default_float
            )


# Test 4: NumberPrompt negative toggle idempotence
@given(
    initial_val=st.integers(min_value=0, max_value=1000)
)
def test_number_prompt_negative_toggle_idempotence(initial_val):
    """Toggling negative twice should return to original value."""
    prompt = NumberPrompt(
        message="Test",
        default=initial_val
    )
    
    # Set initial value in buffer
    prompt._whole_buffer.text = str(initial_val)
    original = prompt._whole_buffer.text
    
    # Toggle negative once
    prompt._handle_negative_toggle(None)
    assert prompt._whole_buffer.text == f"-{original}"
    
    # Toggle negative again
    prompt._handle_negative_toggle(None)
    assert prompt._whole_buffer.text == original


# Test 5: InputPrompt default type constraint
@given(
    valid_default=st.text(min_size=0, max_size=100),
    invalid_default=st.one_of(
        st.integers(),
        st.floats(allow_nan=False),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    )
)
def test_input_prompt_default_type_constraint(valid_default, invalid_default):
    """InputPrompt default must be a string type."""
    
    # Valid string defaults should work
    prompt = InputPrompt(
        message="Test",
        default=valid_default
    )
    assert prompt._default == valid_default
    
    # Non-string defaults should raise InvalidArgument
    if not isinstance(invalid_default, str):
        with pytest.raises(InvalidArgument, match="default.*should be type of str"):
            InputPrompt(
                message="Test",
                default=invalid_default
            )


# Test 6: NumberPrompt value parsing round-trip
@given(
    test_int=st.integers(min_value=-10000, max_value=10000)
)
def test_number_prompt_integer_value_parsing(test_int):
    """Integer value parsing should be consistent."""
    prompt = NumberPrompt(
        message="Test",
        float_allowed=False
    )
    
    # Set value through buffer
    prompt._whole_buffer.text = str(test_int)
    
    # Get value through property
    parsed_value = prompt.value
    
    # Should parse correctly
    assert parsed_value == test_int
    assert isinstance(parsed_value, int)


# Test 7: NumberPrompt float value parsing round-trip
@given(
    whole=st.integers(min_value=-1000, max_value=1000),
    decimal=st.integers(min_value=0, max_value=999999)
)
def test_number_prompt_float_value_parsing(whole, decimal):
    """Float value parsing should correctly combine whole and decimal parts."""
    prompt = NumberPrompt(
        message="Test",
        float_allowed=True
    )
    
    # Set values through buffers
    prompt._whole_buffer.text = str(whole)
    prompt._integral_buffer.text = str(decimal)
    
    # Get value through property
    parsed_value = prompt.value
    
    # Should parse correctly as Decimal
    expected = Decimal(f"{whole}.{decimal}")
    assert parsed_value == expected
    assert isinstance(parsed_value, Decimal)


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))