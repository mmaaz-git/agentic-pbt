#!/usr/bin/env python3
"""Debug the separator index increment bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from InquirerPy.base.control import InquirerPyUIListControl
from InquirerPy.separator import Separator
from typing import List, Tuple, Dict, Any


class TestListControl(InquirerPyUIListControl):
    """Concrete implementation for testing."""
    
    def _get_hover_text(self, choice: Dict[str, Any]) -> List[Tuple[str, str]]:
        return [("class:hover", f"> {choice['name']}")]
    
    def _get_normal_text(self, choice: Dict[str, Any]) -> List[Tuple[str, str]]:
        return [("class:normal", f"  {choice['name']}")]


def test_specific_case():
    """Test a specific failing case from hypothesis."""
    print("Testing separator index increment logic...")
    print("=" * 60)
    
    # Create a simple test case with separator at index 0
    sep1 = Separator("--- Section 1 ---")
    choices = [
        sep1,  # Index 0 - separator
        "Choice 1",  # Index 1 - regular choice
        "Choice 2",  # Index 2 - regular choice
    ]
    
    print(f"Choices: {choices}")
    print(f"Using separator at index 0 as default: {sep1}")
    
    # According to lines 106-109 in control.py:
    # if self.selected_choice_index == index:
    #     self.selected_choice_index = (
    #         self.selected_choice_index + 1
    #     ) % len(choices)
    
    control = TestListControl(choices=choices, default=sep1)
    
    print(f"\nSelected index: {control.selected_choice_index}")
    print(f"Selected choice: {control.choices[control.selected_choice_index]}")
    
    # The selected index should be 1 (first non-separator)
    expected_idx = 1
    actual_idx = control.selected_choice_index
    
    if actual_idx != expected_idx:
        print(f"\n❌ BUG FOUND!")
        print(f"Expected index: {expected_idx}")
        print(f"Actual index: {actual_idx}")
        print(f"Expected to select: 'Choice 1' at index 1")
        print(f"Actually selected: {control.choices[actual_idx]}")
        return False
    else:
        print(f"\n✓ Test passed - correctly skipped separator")
        return True


def test_all_separators_except_last():
    """Test when all items except last are separators."""
    print("\n" + "=" * 60)
    print("Testing case with multiple separators...")
    
    choices = [
        Separator("Sep 1"),  # Index 0
        Separator("Sep 2"),  # Index 1 
        Separator("Sep 3"),  # Index 2
        "Choice Last",  # Index 3
    ]
    
    print(f"Choices: {[str(c) for c in choices]}")
    
    # Test with first separator as default
    control = TestListControl(choices=choices, default=choices[0])
    
    print(f"Selected index: {control.selected_choice_index}")
    print(f"Selected choice: {control.choices[control.selected_choice_index]}")
    
    # Should select index 3 (the only non-separator)
    expected_idx = 3
    actual_idx = control.selected_choice_index
    
    if actual_idx != expected_idx:
        print(f"\n❌ BUG FOUND!")
        print(f"Expected index: {expected_idx}")
        print(f"Actual index: {actual_idx}")
        return False
    else:
        print(f"\n✓ Test passed")
        return True


def test_separator_in_middle():
    """Test separator in middle position."""
    print("\n" + "=" * 60)
    print("Testing separator in middle...")
    
    sep = Separator("--- Middle ---")
    choices = [
        "Choice 0",
        "Choice 1",
        sep,  # Index 2
        "Choice 3",
        "Choice 4",
    ]
    
    print(f"Choices: {choices}")
    print(f"Using separator at index 2 as default")
    
    control = TestListControl(choices=choices, default=sep)
    
    print(f"Selected index: {control.selected_choice_index}")
    print(f"Selected choice: {control.choices[control.selected_choice_index]}")
    
    # According to the code, should increment to (2+1) % 5 = 3
    expected_idx = 3
    actual_idx = control.selected_choice_index
    
    if actual_idx != expected_idx:
        print(f"\n❌ BUG FOUND!")
        print(f"Expected index: {expected_idx}")
        print(f"Actual index: {actual_idx}")
        return False
    else:
        print(f"\n✓ Test passed")
        return True


def test_wrap_around():
    """Test wrap-around when separator is at the end."""
    print("\n" + "=" * 60)
    print("Testing wrap-around case...")
    
    sep = Separator("--- End ---")
    choices = [
        "Choice 0",
        "Choice 1",
        "Choice 2",
        sep,  # Index 3 (last)
    ]
    
    print(f"Choices: {choices}")
    print(f"Using separator at index 3 (last) as default")
    
    control = TestListControl(choices=choices, default=sep)
    
    print(f"Selected index: {control.selected_choice_index}")
    print(f"Selected choice: {control.choices[control.selected_choice_index]}")
    
    # Should wrap to (3+1) % 4 = 0
    expected_idx = 0
    actual_idx = control.selected_choice_index
    
    if actual_idx != expected_idx:
        print(f"\n❌ BUG FOUND!")
        print(f"Expected index: {expected_idx}")
        print(f"Actual index: {actual_idx}")
        return False
    else:
        print(f"\n✓ Test passed")
        return True


def main():
    print("Debugging Separator Index Increment Logic")
    print("=" * 60)
    
    all_passed = True
    
    all_passed &= test_specific_case()
    all_passed &= test_all_separators_except_last()
    all_passed &= test_separator_in_middle()
    all_passed &= test_wrap_around()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed - potential bug found!")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())