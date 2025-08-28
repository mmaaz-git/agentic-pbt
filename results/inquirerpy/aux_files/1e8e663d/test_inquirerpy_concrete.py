#!/usr/bin/env python3
"""Property-based tests for InquirerPy.base module with concrete implementations."""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, Verbosity
import traceback
from typing import List, Tuple, Dict, Any

# Import the modules we're testing
from InquirerPy.base.control import Choice, InquirerPyUIListControl
from InquirerPy.base.complex import FakeDocument
from InquirerPy.separator import Separator


# Create a concrete implementation for testing
class TestListControl(InquirerPyUIListControl):
    """Concrete implementation of InquirerPyUIListControl for testing."""
    
    def _get_hover_text(self, choice: Dict[str, Any]) -> List[Tuple[str, str]]:
        """Simple implementation for testing."""
        return [("class:hover", f"> {choice['name']}")]
    
    def _get_normal_text(self, choice: Dict[str, Any]) -> List[Tuple[str, str]]:
        """Simple implementation for testing."""
        return [("class:normal", f"  {choice['name']}")]


# Test 1: Choice class name defaulting
@given(
    value=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.booleans(),
        st.none(),
        st.lists(st.integers(), max_size=5),
        st.dictionaries(st.text(max_size=3), st.integers(), max_size=3)
    ),
    enabled=st.booleans()
)
@settings(max_examples=200, verbosity=Verbosity.quiet, deadline=5000)
def test_choice_name_defaults(value, enabled):
    """When Choice.name is None, it should default to str(value)"""
    choice = Choice(value=value, name=None, enabled=enabled)
    assert choice.name == str(value), f"Expected name={str(value)}, got {choice.name}"
    assert choice.value == value
    assert choice.enabled == enabled


# Test 2: Test separator index skipping
@given(
    choices_data=st.lists(
        st.one_of(
            st.tuples(st.just("choice"), st.integers()),
            st.tuples(st.just("separator"), st.text())
        ),
        min_size=2,
        max_size=10
    )
)
@settings(max_examples=200, verbosity=Verbosity.quiet, deadline=5000)
def test_separator_skipping(choices_data):
    """Control should skip separator when it's the default"""
    # Ensure at least one non-separator
    has_choice = any(c[0] == "choice" for c in choices_data)
    if not has_choice:
        choices_data.append(("choice", 999))
    
    choices = []
    for typ, val in choices_data:
        if typ == "separator":
            choices.append(Separator(val))
        else:
            choices.append({"name": f"Choice {val}", "value": val})
    
    # Test with first item as default
    if isinstance(choices[0], Separator):
        default = choices[0]
    else:
        default = choices[0]["value"]
        
    control = TestListControl(choices=choices, default=default)
    
    # Selected index should never point to a separator
    selected = control.choices[control.selected_choice_index]["value"]
    assert not isinstance(selected, Separator), f"Selected index points to separator"
    
    # Check bounds
    assert 0 <= control.selected_choice_index < len(control.choices)


# Test 3: FakeDocument preservation
@given(
    text=st.text(),
    cursor_pos=st.integers(min_value=-1000, max_value=1000)
)
@settings(max_examples=200, verbosity=Verbosity.quiet, deadline=5000)
def test_fake_document(text, cursor_pos):
    """FakeDocument should preserve its fields"""
    doc = FakeDocument(text=text, cursor_position=cursor_pos)
    assert doc.text == text, f"Text not preserved: expected {text}, got {doc.text}"
    assert doc.cursor_position == cursor_pos, f"Cursor not preserved"


# Test 4: Choice count invariant
@given(
    num_choices=st.integers(min_value=1, max_value=20),
    num_seps=st.integers(min_value=0, max_value=10)
)
@settings(max_examples=200, verbosity=Verbosity.quiet, deadline=5000)
def test_choice_count(num_choices, num_seps):
    """choice_count should equal len(choices)"""
    choices = []
    for i in range(num_choices):
        choices.append(f"Choice {i}")
    for i in range(num_seps):
        choices.append(Separator(f"Sep {i}"))
        
    control = TestListControl(choices=choices)
    
    expected = num_choices + num_seps
    assert control.choice_count == expected, f"Expected {expected}, got {control.choice_count}"
    assert control.choice_count == len(control.choices)


# Test 5: Choice with extreme values
@given(
    value=st.one_of(
        st.floats(allow_nan=True, allow_infinity=True),
        st.text(alphabet="", min_size=0, max_size=0),  # empty string
        st.lists(st.integers(), min_size=0, max_size=0),  # empty list
        st.dictionaries(st.text(), st.integers(), min_size=0, max_size=0),  # empty dict
    )
)
@settings(max_examples=200, verbosity=Verbosity.quiet, deadline=5000)
def test_choice_edge_cases(value):
    """Choice should handle edge case values"""
    choice = Choice(value=value, name=None, enabled=False)
    # Should successfully create and stringify
    assert isinstance(choice.name, str), f"Name should be string, got {type(choice.name)}"
    # Handle NaN case specially
    if value != value:  # NaN check
        assert choice.value != choice.value  # Should preserve NaN
    else:
        assert choice.value == value


# Test 6: Testing index wrapping behavior
@given(
    num_choices=st.integers(min_value=2, max_value=10),
    increments=st.integers(min_value=0, max_value=100)
)
@settings(max_examples=200, verbosity=Verbosity.quiet, deadline=5000)
def test_index_wrapping(num_choices, increments):
    """Test that index wrapping with modulo works correctly"""
    choices = [f"Choice {i}" for i in range(num_choices)]
    control = TestListControl(choices=choices)
    
    initial_index = control.selected_choice_index
    
    # Simulate incrementing the index (like moving down)
    new_index = (initial_index + increments) % num_choices
    control.selected_choice_index = new_index
    
    # Check it's within bounds
    assert 0 <= control.selected_choice_index < num_choices
    assert control.selected_choice_index == new_index


# Test 7: Testing multiselect enabled flag preservation
@given(
    values=st.lists(st.integers(), min_size=1, max_size=5),
    enabled_flags=st.lists(st.booleans(), min_size=1, max_size=5)
)
@settings(max_examples=200, verbosity=Verbosity.quiet, deadline=5000)
def test_multiselect_enabled_preservation(values, enabled_flags):
    """In multiselect mode, enabled flags should be preserved"""
    # Make same length
    min_len = min(len(values), len(enabled_flags))
    values = values[:min_len]
    enabled_flags = enabled_flags[:min_len]
    
    choices = []
    for v, e in zip(values, enabled_flags):
        choices.append({"name": f"Item {v}", "value": v, "enabled": e})
    
    control = TestListControl(choices=choices, multiselect=True)
    
    # Check enabled flags are preserved
    for i, choice in enumerate(control.choices):
        if not isinstance(choice["value"], Separator):
            assert choice["enabled"] == enabled_flags[i], f"Enabled flag not preserved at index {i}"


# Test 8: Index out of bounds protection
@given(
    all_separators=st.booleans()
)
@settings(max_examples=50, verbosity=Verbosity.quiet, deadline=5000)
def test_all_separators_error(all_separators):
    """Control should raise error if all choices are separators"""
    from InquirerPy.exceptions import InvalidArgument
    
    if all_separators:
        # Create choices with only separators
        choices = [Separator(f"Sep {i}") for i in range(5)]
        
        try:
            control = TestListControl(choices=choices)
            assert False, "Should have raised InvalidArgument"
        except InvalidArgument as e:
            assert "should contain choices other than separator" in str(e)
    else:
        # At least one non-separator
        choices = [Separator("Sep"), "Choice 1", Separator("Sep2")]
        control = TestListControl(choices=choices)
        # Should not raise


# Test 9: Test selection property
@given(
    num_choices=st.integers(min_value=1, max_value=10),
    selected_idx=st.integers(min_value=0, max_value=9)
)
@settings(max_examples=200, verbosity=Verbosity.quiet, deadline=5000)
def test_selection_property(num_choices, selected_idx):
    """selection property should return the currently selected choice"""
    assume(selected_idx < num_choices)
    
    choices = [{"name": f"Choice {i}", "value": i} for i in range(num_choices)]
    control = TestListControl(choices=choices)
    control.selected_choice_index = selected_idx
    
    assert control.selection == control.choices[selected_idx]
    assert control.selection["value"] == selected_idx


# Test 10: Separator in default causes index increment modulo
@given(
    sep_positions=st.lists(st.integers(min_value=0, max_value=4), min_size=1, max_size=5, unique=True)
)
@settings(max_examples=200, verbosity=Verbosity.quiet, deadline=5000)
def test_separator_index_increment_modulo(sep_positions):
    """When default is separator at index i, selected should be (i+1) % len"""
    choices = []
    for i in range(5):
        if i in sep_positions:
            choices.append(Separator(f"Sep {i}"))
        else:
            choices.append(f"Choice {i}")
    
    # Ensure at least one non-separator
    if all(isinstance(c, Separator) for c in choices):
        choices.append("Choice Last")
    
    # Use first separator as default if exists
    first_sep_idx = None
    for i, c in enumerate(choices):
        if isinstance(c, Separator):
            first_sep_idx = i
            break
    
    if first_sep_idx is not None:
        control = TestListControl(choices=choices, default=choices[first_sep_idx])
        
        # Check that selected index is not the separator
        assert not isinstance(control.choices[control.selected_choice_index]["value"], Separator)
        
        # Check the modulo increment logic (lines 107-109 in control.py)
        expected_idx = first_sep_idx
        while isinstance(control.choices[expected_idx]["value"], Separator):
            expected_idx = (expected_idx + 1) % len(control.choices)
        
        assert control.selected_choice_index == expected_idx


def main():
    """Run all tests."""
    print("=" * 70)
    print("Property-Based Testing for InquirerPy.base")
    print("=" * 70)
    
    tests = [
        test_choice_name_defaults,
        test_separator_skipping,
        test_fake_document,
        test_choice_count,
        test_choice_edge_cases,
        test_index_wrapping,
        test_multiselect_enabled_preservation,
        test_all_separators_error,
        test_selection_property,
        test_separator_index_increment_modulo,
    ]
    
    failed = []
    
    for test_func in tests:
        test_name = test_func.__name__
        print(f"\nRunning: {test_name}")
        try:
            test_func()
            print(f"  ✓ {test_name} PASSED")
        except AssertionError as e:
            print(f"  ✗ {test_name} FAILED")
            print(f"    Failure: {e}")
            failed.append((test_name, e))
        except Exception as e:
            print(f"  ✗ {test_name} ERROR")
            print(f"    Error: {e}")
            traceback.print_exc()
            failed.append((test_name, e))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    total = len(tests)
    passed = total - len(failed)
    print(f"Tests passed: {passed}/{total}")
    
    if failed:
        print("\nFailed tests:")
        for name, error in failed:
            print(f"  ✗ {name}")
        return 1
    else:
        print("\n✅ All tests passed! No bugs found in InquirerPy.base module.")
        return 0


if __name__ == "__main__":
    sys.exit(main())