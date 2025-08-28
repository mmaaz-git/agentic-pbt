"""Property-based tests for InquirerPy.base module."""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

import re
from unittest.mock import MagicMock, patch
from hypothesis import given, strategies as st, assume, settings
import pytest

# Import the modules we're testing
from InquirerPy.base.control import Choice, InquirerPyUIListControl
from InquirerPy.base.simple import BaseSimplePrompt
from InquirerPy.base.complex import BaseComplexPrompt, FakeDocument
from InquirerPy.separator import Separator


# Test 1: Choice class name defaulting property
@given(
    value=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.booleans(),
        st.none(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    ),
    enabled=st.booleans()
)
def test_choice_name_defaults_to_str_value(value, enabled):
    """When Choice.name is None, it should default to str(value) - lines 36-37 in control.py"""
    choice = Choice(value=value, name=None, enabled=enabled)
    assert choice.name == str(value)
    assert choice.value == value
    assert choice.enabled == enabled


@given(
    value=st.one_of(st.integers(), st.text(), st.floats(allow_nan=False)),
    name=st.text(),
    enabled=st.booleans()
)
def test_choice_preserves_explicit_name(value, name, enabled):
    """When Choice.name is provided, it should be preserved"""
    choice = Choice(value=value, name=name, enabled=enabled)
    assert choice.name == name
    assert choice.value == value
    assert choice.enabled == enabled


# Test 2: InquirerPyUIListControl index management with separators
@given(
    num_choices=st.integers(min_value=2, max_value=20),
    separator_positions=st.lists(st.integers(min_value=0, max_value=19), max_size=5),
    default_index=st.integers(min_value=0, max_value=19)
)
def test_control_separator_index_skipping(num_choices, separator_positions, default_index):
    """When default matches a Separator, index should increment - lines 106-109 in control.py"""
    assume(default_index < num_choices)
    
    # Create choices with some separators
    choices = []
    for i in range(num_choices):
        if i in separator_positions:
            choices.append(Separator(f"--- Section {i} ---"))
        else:
            choices.append({"name": f"Choice {i}", "value": i})
    
    # Make sure we have at least one non-separator choice
    assume(len([c for c in choices if not isinstance(c, Separator)]) > 0)
    
    # If default_index points to a separator, use None as default (to trigger the separator skip logic)
    if default_index in separator_positions:
        default_value = choices[default_index]
    else:
        default_value = default_index
    
    control = InquirerPyUIListControl(choices=choices, default=default_value)
    
    # The selected index should never be on a separator
    assert not isinstance(control.choices[control.selected_choice_index]["value"], Separator)
    
    # Check bounds
    assert 0 <= control.selected_choice_index < len(control.choices)


# Test 3: BaseSimplePrompt alt key transformation
@given(
    key_suffix=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-=[]\\;',./", min_size=1, max_size=5)
)
def test_alt_key_transformation(key_suffix):
    """Alt keys should be transformed to escape + key - lines 226-236 in simple.py"""
    
    # Create a minimal concrete subclass for testing
    class TestPrompt(BaseSimplePrompt):
        def _set_error(self, message: str) -> None:
            pass
        
        def _handle_enter(self, event) -> None:
            pass
        
        def _get_prompt_message(self, pre_answer, post_answer):
            return super()._get_prompt_message(pre_answer, post_answer)
        
        def _run(self):
            return None
        
        async def _run_async(self):
            return None
    
    prompt = TestPrompt(message="Test", default="")
    
    # Track what keys were registered
    registered_keys = []
    original_add = prompt._kb.add
    
    def mock_add(*keys, **kwargs):
        registered_keys.extend(keys)
        return lambda f: f
    
    prompt._kb.add = mock_add
    
    # Register an alt key
    alt_key = f"alt-{key_suffix}"
    
    @prompt.register_kb(alt_key)
    def test_handler(event):
        pass
    
    # Check the transformation happened
    assert "escape" in registered_keys
    assert key_suffix in registered_keys


# Test 4: BaseComplexPrompt line wrapping calculations
@given(
    message_length=st.integers(min_value=1, max_value=500),
    terminal_width=st.integers(min_value=10, max_value=200)
)
def test_extra_line_count_calculation(message_length, terminal_width):
    """Extra line count should be calculated correctly - lines 261-262 in complex.py"""
    
    class TestComplexPrompt(BaseComplexPrompt):
        def _handle_enter(self, event):
            pass
        
        def _on_rendered(self, app):
            pass
            
        def _run(self):
            return None
        
        async def _run_async(self):
            return None
    
    with patch('shutil.get_terminal_size', return_value=(terminal_width, 24)):
        prompt = TestComplexPrompt(
            message="x" * message_length,
            qmark="?",
            instruction=""
        )
        
        # Override total_message_length for testing
        prompt._message = "x" * message_length
        prompt._qmark = "?"
        prompt._instruction = ""
        
        # The formula from the code: (total_length - 1) // term_width
        # With qmark "?" and space, plus message
        total_length = len("?") + 1 + message_length + 1  # qmark + space + message + space
        expected_extra_lines = (total_length - 1) // terminal_width
        
        # Check that extra_message_line_count matches expectation
        assert prompt.extra_message_line_count == expected_extra_lines
        assert prompt.extra_message_line_count >= 0


# Test 5: FakeDocument dataclass
@given(
    text=st.text(),
    cursor_pos=st.integers()
)
def test_fake_document_preserves_data(text, cursor_pos):
    """FakeDocument should preserve text and cursor_position"""
    doc = FakeDocument(text=text, cursor_position=cursor_pos)
    assert doc.text == text
    assert doc.cursor_position == cursor_pos


# Test 6: Choice dict roundtrip through InquirerPyUIListControl._get_choices
@given(
    values=st.lists(
        st.one_of(st.integers(), st.text(min_size=1), st.floats(allow_nan=False)),
        min_size=1,
        max_size=10
    ),
    names=st.lists(st.text(min_size=1), min_size=1, max_size=10)
)
def test_control_preserves_choice_data(values, names):
    """InquirerPyUIListControl should preserve choice data correctly"""
    # Make lists same length
    min_len = min(len(values), len(names))
    values = values[:min_len]
    names = names[:min_len]
    
    choices = []
    for v, n in zip(values, names):
        choices.append({"name": n, "value": v})
    
    control = InquirerPyUIListControl(choices=choices)
    
    # Check all choices were preserved
    assert len(control.choices) == len(choices)
    for i, choice in enumerate(control.choices):
        assert choice["name"] == names[i]
        assert choice["value"] == values[i]
        assert choice["enabled"] == False  # Default when not multiselect


# Test 7: Control choice count property
@given(
    num_regular=st.integers(min_value=1, max_value=20),
    num_separators=st.integers(min_value=0, max_value=10)
)
def test_control_choice_count(num_regular, num_separators):
    """choice_count should equal total number of choices including separators"""
    choices = []
    
    # Add regular choices
    for i in range(num_regular):
        choices.append(f"Choice {i}")
    
    # Add separators
    for i in range(num_separators):
        choices.append(Separator(f"Sep {i}"))
    
    control = InquirerPyUIListControl(choices=choices)
    
    assert control.choice_count == num_regular + num_separators
    assert control.choice_count == len(control.choices)


if __name__ == "__main__":
    print("Running property-based tests for InquirerPy.base module...")
    pytest.main([__file__, "-v"])