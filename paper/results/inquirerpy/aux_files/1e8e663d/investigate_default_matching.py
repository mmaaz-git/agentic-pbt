#!/usr/bin/env python3
"""Investigate how default matching works with separators."""

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


def test_separator_matching():
    """Test how separator matching works in _get_choices."""
    print("Testing separator default matching logic...")
    print("=" * 60)
    
    # Looking at control.py lines 105-112:
    # elif isinstance(choice, Separator):
    #     if self.selected_choice_index == index:
    #         self.selected_choice_index = (
    #             self.selected_choice_index + 1
    #         ) % len(choices)
    
    # The issue is that the code checks if self.selected_choice_index == index
    # But selected_choice_index starts at 0, and is only modified if:
    # 1. choice["value"] == default (line 94)
    # 2. choice == default (line 121)  
    # 3. It's a separator AND selected_choice_index == index (lines 106-109)
    
    sep = Separator("--- Test ---")
    choices = [
        "Choice 0",  # Index 0
        "Choice 1",  # Index 1
        sep,         # Index 2 - separator
        "Choice 3",  # Index 3
    ]
    
    print(f"Testing with separator object as default...")
    print(f"Separator: {sep}")
    print(f"Choices: {choices}")
    
    # When we pass the separator object as default
    control = TestListControl(choices=choices, default=sep)
    
    print(f"\nAfter initialization:")
    print(f"  Selected index: {control.selected_choice_index}")
    print(f"  Selected choice value: {control.choices[control.selected_choice_index]['value']}")
    
    # Let's trace through what should happen:
    # 1. selected_choice_index starts at 0
    # 2. For choice at index 0 ("Choice 0"):
    #    - It's not a dict, goes to else block (line 120)
    #    - choice == default? "Choice 0" == sep? No
    #    - selected_choice_index stays 0
    # 3. For choice at index 1 ("Choice 1"):
    #    - Same as above, no match
    # 4. For choice at index 2 (sep):
    #    - isinstance(choice, Separator)? Yes (line 105)
    #    - self.selected_choice_index == index? 0 == 2? No!
    #    - So the increment doesn't happen!
    
    print("\n🔍 Analysis:")
    print("The bug is that when a Separator is passed as default,")
    print("the code doesn't properly set selected_choice_index to that separator's index.")
    print("It only increments if selected_choice_index already equals the separator's index,")
    print("which won't happen unless it was already set to that index by a previous match.")
    
    # Test another way - what if we set default to None but manually set index?
    print("\n" + "=" * 60)
    print("Testing with no default (should stay at 0)...")
    control2 = TestListControl(choices=choices)
    print(f"Selected index: {control2.selected_choice_index}")
    
    # Now manually set to separator index
    control2.selected_choice_index = 2
    print(f"After manually setting to separator index 2: {control2.selected_choice_index}")
    # Note: The increment only happens during initialization, not after


def test_correct_behavior():
    """Test what the correct behavior should be."""
    print("\n" + "=" * 60)
    print("Testing expected correct behavior...")
    
    sep = Separator("--- Test ---")
    choices = [
        "Choice 0",
        sep,
        "Choice 2",
    ]
    
    print(f"Choices: {choices}")
    print(f"If separator at index 1 is default, should select index 2")
    
    # The current implementation doesn't handle this correctly
    control = TestListControl(choices=choices, default=sep)
    print(f"Actual selected index: {control.selected_choice_index}")
    print(f"Expected: 2, Got: {control.selected_choice_index}")
    
    if control.selected_choice_index != 2:
        print("❌ BUG CONFIRMED: Separator as default doesn't work correctly!")
        print("\nThe issue is in the _get_choices method:")
        print("When a Separator object is passed as 'default', it's never matched")
        print("because the code compares with == but Separators don't have proper equality.")
        return False
    return True


def test_separator_equality():
    """Test separator equality."""
    print("\n" + "=" * 60)
    print("Testing Separator equality...")
    
    sep1 = Separator("Test")
    sep2 = Separator("Test")
    sep3 = sep1
    
    print(f"sep1 = Separator('Test')")
    print(f"sep2 = Separator('Test')")
    print(f"sep3 = sep1")
    print(f"\nsep1 == sep2: {sep1 == sep2}")
    print(f"sep1 is sep2: {sep1 is sep2}")
    print(f"sep1 == sep3: {sep1 == sep3}")
    print(f"sep1 is sep3: {sep1 is sep3}")
    
    # This confirms separators use identity equality by default
    if sep1 != sep2:
        print("\n⚠️ Separators with same text are not equal!")
        print("This means passing a Separator as default only works if it's the exact same object.")


def main():
    print("Investigation: Default Matching with Separators")
    print("=" * 60)
    
    test_separator_matching()
    test_correct_behavior()
    test_separator_equality()
    
    print("\n" + "=" * 60)
    print("CONCLUSION:")
    print("Bug found in InquirerPy.base.control.InquirerPyUIListControl._get_choices")
    print("When a Separator is used as the default value, the selected index")
    print("is not properly set to skip over that separator.")
    
    return 1


if __name__ == "__main__":
    sys.exit(main())