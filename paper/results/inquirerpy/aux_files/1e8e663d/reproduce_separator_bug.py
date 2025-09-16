#!/usr/bin/env python3
"""Minimal reproduction of the separator default bug in InquirerPy."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from InquirerPy.base.control import InquirerPyUIListControl
from InquirerPy.separator import Separator
from typing import List, Tuple, Dict, Any


class ConcreteListControl(InquirerPyUIListControl):
    def _get_hover_text(self, choice: Dict[str, Any]) -> List[Tuple[str, str]]:
        return [("", f"> {choice['name']}")]
    
    def _get_normal_text(self, choice: Dict[str, Any]) -> List[Tuple[str, str]]:
        return [("", f"  {choice['name']}")]


# Reproduce the bug
separator = Separator("--- Section ---")
choices = [
    "Option A",
    separator,  # This separator at index 1
    "Option B",
]

# Using the separator as default should skip to next non-separator (index 2)
control = ConcreteListControl(choices=choices, default=separator)

# Bug: selected_choice_index is 0 instead of 2
print(f"Selected index: {control.selected_choice_index}")
print(f"Selected choice: {control.choices[control.selected_choice_index]['value']}")
print(f"Expected index: 2 (Option B)")
print(f"Actual index: {control.selected_choice_index} ({control.choices[control.selected_choice_index]['value']})")

assert control.selected_choice_index == 2, f"Bug: Expected index 2, got {control.selected_choice_index}"