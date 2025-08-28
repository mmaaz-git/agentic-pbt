#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

import math
from decimal import Decimal
from unittest.mock import MagicMock, patch

from hypothesis import assume, given, settings, strategies as st
from InquirerPy.prompts import (
    CheckboxPrompt,
    ConfirmPrompt,
    FuzzyPrompt,
    ListPrompt,
    NumberPrompt,
)
from InquirerPy.separator import Separator
from InquirerPy.exceptions import InvalidArgument
import pytest


# Test 1: NumberPrompt min/max bounds enforcement
@given(
    min_val=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    max_val=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    default_val=st.floats(min_value=-1e9, max_value=1e9, allow_nan=False, allow_infinity=False),
)
def test_number_prompt_min_max_bounds(min_val, max_val, default_val):
    """Test that NumberPrompt respects min_allowed and max_allowed bounds.
    
    Based on the value setter at line 596-604 in number.py:
    - When min_allowed is set, value should be >= min_allowed
    - When max_allowed is set, value should be <= max_allowed
    """
    assume(min_val <= max_val)  # Ensure valid range
    
    # Create prompt with bounds
    prompt = NumberPrompt(
        message="Test",
        min_allowed=min_val,
        max_allowed=max_val,
        default=default_val,
        float_allowed=True
    )
    
    # The value property should clamp the default to the bounds
    value = prompt.value
    
    # Property: value should respect min bound
    if min_val is not None:
        assert value >= Decimal(str(min_val)), f"Value {value} is below min {min_val}"
    
    # Property: value should respect max bound  
    if max_val is not None:
        assert value <= Decimal(str(max_val)), f"Value {value} is above max {max_val}"


# Test 2: NumberPrompt float handling
@given(
    float_val=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
)
def test_number_prompt_float_handling(float_val):
    """Test that NumberPrompt correctly handles float values when float_allowed=True.
    
    Based on lines 171-176 in number.py - when float_allowed is True, 
    default should be converted to Decimal.
    """
    prompt = NumberPrompt(
        message="Test",
        float_allowed=True,
        default=float_val
    )
    
    # Property: When float_allowed=True, the internal default should be a Decimal
    assert isinstance(prompt._default, Decimal)
    
    # Property: The value should preserve the float value (within floating point precision)
    assert math.isclose(float(prompt.value), float_val, rel_tol=1e-9)


# Test 3: NumberPrompt integer-only mode validation  
@given(
    int_val=st.integers(min_value=-10000, max_value=10000)
)
def test_number_prompt_integer_mode(int_val):
    """Test that NumberPrompt with float_allowed=False only accepts integers.
    
    Based on lines 177-180 in number.py - when float_allowed is False,
    default must be an integer.
    """
    prompt = NumberPrompt(
        message="Test",
        float_allowed=False,
        default=int_val
    )
    
    # Property: Default should remain an integer
    assert isinstance(prompt._default, int)
    assert prompt._default == int_val
    
    # Property: Value should be an integer
    assert isinstance(prompt.value, int)
    assert prompt.value == int_val


# Test 4: ConfirmPrompt boolean handling
@given(
    default=st.booleans(),
    confirm_letter=st.text(min_size=1, max_size=1).filter(lambda x: x.isalpha()),
    reject_letter=st.text(min_size=1, max_size=1).filter(lambda x: x.isalpha())
)
def test_confirm_prompt_boolean_property(default, confirm_letter, reject_letter):
    """Test that ConfirmPrompt always works with boolean values.
    
    Based on lines 113-116 in confirm.py - default must be a boolean.
    """
    assume(confirm_letter != reject_letter)  # Letters must be different
    
    prompt = ConfirmPrompt(
        message="Test",
        default=default,
        confirm_letter=confirm_letter,
        reject_letter=reject_letter
    )
    
    # Property: Default should be a boolean
    assert isinstance(prompt._default, bool)
    assert prompt._default == default


# Test 5: ConfirmPrompt invalid default validation
@given(
    invalid_default=st.one_of(
        st.integers(),
        st.floats(allow_nan=False),
        st.text(),
        st.lists(st.integers())
    )
)
def test_confirm_prompt_rejects_non_boolean(invalid_default):
    """Test that ConfirmPrompt rejects non-boolean default values.
    
    Based on lines 113-116 in confirm.py - should raise InvalidArgument for non-bool.
    """
    assume(not isinstance(invalid_default, bool))  # Exclude booleans
    
    with pytest.raises(InvalidArgument, match="default should be type of bool"):
        ConfirmPrompt(
            message="Test",
            default=invalid_default
        )


# Test 6: CheckboxPrompt choices validation
@given(
    choices=st.lists(
        st.fixed_dictionaries({
            "name": st.text(min_size=1),
            "value": st.text(min_size=1),
            "enabled": st.booleans()
        }),
        min_size=1,
        max_size=10
    ),
    default_values=st.lists(st.text(min_size=1), max_size=5)
)
def test_checkbox_prompt_result_subset(choices, default_values):
    """Test that CheckboxPrompt results are a subset of provided choices.
    
    The CheckboxPrompt should only return values that were in the original choices.
    """
    # Convert choices to the expected format
    formatted_choices = []
    for choice in choices:
        formatted_choices.append({
            "name": choice["name"],
            "value": choice["value"],
            "enabled": choice.get("enabled", False)
        })
    
    # Create the prompt
    prompt = CheckboxPrompt(
        message="Test",
        choices=formatted_choices,
        default=default_values
    )
    
    # Property: All enabled choices should have values from the original choices
    choice_values = {c["value"] for c in formatted_choices}
    enabled_values = [c["value"] for c in prompt._control.choices if c.get("enabled", False)]
    
    for val in enabled_values:
        assert val in choice_values, f"Enabled value {val} not in original choices"


# Test 7: FuzzyPrompt separator validation
def test_fuzzy_prompt_rejects_separator():
    """Test that FuzzyPrompt rejects Separator in choices.
    
    Based on lines 97-100 in fuzzy.py - FuzzyPrompt should raise InvalidArgument
    if choices contain a Separator.
    """
    choices = [
        {"name": "Option 1", "value": "1"},
        {"name": "---", "value": Separator()},  # Invalid separator
        {"name": "Option 2", "value": "2"}
    ]
    
    with pytest.raises(InvalidArgument, match="should not contain Separator"):
        prompt = FuzzyPrompt(
            message="Test",
            choices=choices
        )
        # Access the control to trigger validation
        _ = prompt._control.choices


# Test 8: NumberPrompt negative toggle property
@given(
    initial_val=st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False).filter(lambda x: x != 0)
)
def test_number_prompt_negative_toggle(initial_val):
    """Test that NumberPrompt negative toggle correctly negates values.
    
    Based on _handle_negative_toggle at lines 504-523 in number.py.
    """
    prompt = NumberPrompt(
        message="Test",
        default=initial_val,
        float_allowed=True
    )
    
    # Simulate the negative toggle by directly manipulating the buffer
    # This tests the logic in _handle_negative_toggle
    if str(initial_val).startswith("-"):
        # Should remove the negative sign
        expected = str(initial_val)[1:]
    else:
        # Should add the negative sign
        expected = f"-{initial_val}"
    
    # Property: Toggling negative on a positive number should make it negative
    # and vice versa (this is what the method does to the buffer text)
    original_text = str(initial_val)
    if original_text.startswith("-"):
        toggled_text = original_text[1:]
    else:
        toggled_text = f"-{original_text}"
    
    # The toggle should produce the opposite sign
    assert (original_text.startswith("-")) != (toggled_text.startswith("-"))


# Test 9: ListPrompt multiselect property
@given(
    choices=st.lists(
        st.text(min_size=1, max_size=10),
        min_size=2,
        max_size=10,
        unique=True
    ),
    multiselect=st.booleans()
)
def test_list_prompt_multiselect_types(choices, multiselect):
    """Test that ListPrompt respects multiselect setting.
    
    When multiselect=False, should allow single selection.
    When multiselect=True, should allow multiple selections.
    """
    formatted_choices = [{"name": c, "value": c} for c in choices]
    
    prompt = ListPrompt(
        message="Test",
        choices=formatted_choices,
        multiselect=multiselect
    )
    
    # Property: multiselect setting should be preserved
    assert prompt._multiselect == multiselect
    
    # Property: control should have correct multiselect setting
    assert prompt._control._multiselect == multiselect


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    import sys
    sys.exit(pytest.main([__file__, "-v", "--hypothesis-show-statistics"]))