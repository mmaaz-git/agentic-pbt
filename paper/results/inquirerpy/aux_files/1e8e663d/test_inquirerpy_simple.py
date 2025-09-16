#!/usr/bin/env python3
"""Direct property-based tests for InquirerPy.base module without pytest."""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, Verbosity
from hypothesis import reproduce_failure
import traceback

# Import the modules we're testing
from InquirerPy.base.control import Choice, InquirerPyUIListControl
from InquirerPy.base.simple import BaseSimplePrompt
from InquirerPy.base.complex import BaseComplexPrompt, FakeDocument
from InquirerPy.separator import Separator


def run_test(test_func, test_name):
    """Run a single property test and report results."""
    print(f"\nTesting: {test_name}")
    print("-" * 60)
    try:
        test_func()
        print(f"✓ {test_name} PASSED")
        return True
    except Exception as e:
        print(f"✗ {test_name} FAILED")
        print(f"  Error: {e}")
        traceback.print_exc()
        return False


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
@settings(max_examples=100, verbosity=Verbosity.quiet)
def test_choice_name_defaults():
    """When Choice.name is None, it should default to str(value)"""
    def inner(value, enabled):
        choice = Choice(value=value, name=None, enabled=enabled)
        assert choice.name == str(value), f"Expected name={str(value)}, got {choice.name}"
        assert choice.value == value
        assert choice.enabled == enabled
    return inner


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
@settings(max_examples=100, verbosity=Verbosity.quiet)
def test_separator_skipping():
    """Control should skip separator when it's the default"""
    def inner(choices_data):
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
            
        control = InquirerPyUIListControl(choices=choices, default=default)
        
        # Selected index should never point to a separator
        selected = control.choices[control.selected_choice_index]["value"]
        assert not isinstance(selected, Separator), f"Selected index points to separator"
        
        # Check bounds
        assert 0 <= control.selected_choice_index < len(control.choices)
    return inner


# Test 3: FakeDocument preservation
@given(
    text=st.text(),
    cursor_pos=st.integers(min_value=-1000, max_value=1000)
)
@settings(max_examples=100, verbosity=Verbosity.quiet)
def test_fake_document():
    """FakeDocument should preserve its fields"""
    def inner(text, cursor_pos):
        doc = FakeDocument(text=text, cursor_position=cursor_pos)
        assert doc.text == text, f"Text not preserved: expected {text}, got {doc.text}"
        assert doc.cursor_position == cursor_pos, f"Cursor not preserved"
    return inner


# Test 4: Choice count invariant
@given(
    num_choices=st.integers(min_value=1, max_value=20),
    num_seps=st.integers(min_value=0, max_value=10)
)
@settings(max_examples=100, verbosity=Verbosity.quiet)
def test_choice_count():
    """choice_count should equal len(choices)"""
    def inner(num_choices, num_seps):
        choices = []
        for i in range(num_choices):
            choices.append(f"Choice {i}")
        for i in range(num_seps):
            choices.append(Separator(f"Sep {i}"))
            
        control = InquirerPyUIListControl(choices=choices)
        
        expected = num_choices + num_seps
        assert control.choice_count == expected, f"Expected {expected}, got {control.choice_count}"
        assert control.choice_count == len(control.choices)
    return inner


# Test 5: Choice with extreme values
@given(
    value=st.one_of(
        st.floats(allow_nan=True, allow_infinity=True),
        st.text(alphabet="", min_size=0, max_size=0),  # empty string
        st.lists(st.integers(), min_size=0, max_size=0),  # empty list
        st.dictionaries(st.text(), st.integers(), min_size=0, max_size=0),  # empty dict
    )
)
@settings(max_examples=100, verbosity=Verbosity.quiet, deadline=1000)
def test_choice_edge_cases():
    """Choice should handle edge case values"""
    def inner(value):
        try:
            choice = Choice(value=value, name=None, enabled=False)
            # Should successfully create and stringify
            assert isinstance(choice.name, str), f"Name should be string, got {type(choice.name)}"
            assert choice.value == value or (value != value and choice.value != choice.value)  # Handle NaN
        except Exception as e:
            # If it fails, that might be a bug
            print(f"Failed on value={value}: {e}")
            raise
    return inner


def main():
    """Run all tests."""
    print("=" * 70)
    print("Property-Based Testing for InquirerPy.base")
    print("=" * 70)
    
    results = []
    
    # Run each test
    tests = [
        (test_choice_name_defaults(), "Choice name defaulting"),
        (test_separator_skipping(), "Separator index skipping"),
        (test_fake_document(), "FakeDocument data preservation"),
        (test_choice_count(), "Choice count invariant"),
        (test_choice_edge_cases(), "Choice edge cases"),
    ]
    
    for test_func, name in tests:
        result = run_test(test_func, name)
        results.append((name, result))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    if passed < total:
        print("\nBugs may have been found! Check the output above for details.")
        return 1
    else:
        print("\nAll tests passed! No bugs found.")
        return 0


if __name__ == "__main__":
    sys.exit(main())