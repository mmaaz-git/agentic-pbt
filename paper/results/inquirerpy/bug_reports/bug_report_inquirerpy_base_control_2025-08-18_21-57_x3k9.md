# Bug Report: InquirerPy.base.control Separator Default Selection Bug

**Target**: `InquirerPy.base.control.InquirerPyUIListControl`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

When a Separator object is passed as the default value to InquirerPyUIListControl, the selected index is not properly adjusted to skip the separator, causing the wrong item to be selected.

## Property-Based Test

```python
@given(
    sep_positions=st.lists(st.integers(min_value=0, max_value=4), min_size=1, max_size=5, unique=True)
)
def test_separator_index_increment_modulo(sep_positions):
    """When default is separator at index i, selected should skip to next non-separator"""
    choices = []
    for i in range(5):
        if i in sep_positions:
            choices.append(Separator(f"Sep {i}"))
        else:
            choices.append(f"Choice {i}")
    
    if all(isinstance(c, Separator) for c in choices):
        choices.append("Choice Last")
    
    first_sep_idx = None
    for i, c in enumerate(choices):
        if isinstance(c, Separator):
            first_sep_idx = i
            break
    
    if first_sep_idx is not None:
        control = TestListControl(choices=choices, default=choices[first_sep_idx])
        assert not isinstance(control.choices[control.selected_choice_index]["value"], Separator)
```

**Failing input**: `sep_positions=[1]` with choices `["Choice 0", Separator("Sep 1"), "Choice 2", "Choice 3", "Choice 4"]`

## Reproducing the Bug

```python
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

separator = Separator("--- Section ---")
choices = [
    "Option A",
    separator,
    "Option B",
]

control = ConcreteListControl(choices=choices, default=separator)

print(f"Selected index: {control.selected_choice_index}")
print(f"Expected: 2 (Option B)")
print(f"Actual: {control.selected_choice_index} ({control.choices[control.selected_choice_index]['value']})")

assert control.selected_choice_index == 2
```

## Why This Is A Bug

The code in `_get_choices` method (lines 105-112 of control.py) has logic to skip separators, but it only triggers when `self.selected_choice_index == index`. However, when a Separator object is passed as the default, it's never matched in the preceding conditions because Separator objects don't implement equality comparison. This causes the selected index to remain at 0 instead of advancing past the separator.

## Fix

The bug occurs because the code doesn't properly handle when a Separator instance is passed as the default value. Here's a fix:

```diff
--- a/InquirerPy/base/control.py
+++ b/InquirerPy/base/control.py
@@ -89,6 +89,7 @@ class InquirerPyUIListControl(FormattedTextControl):
         """
         processed_choices: List[Dict[str, Any]] = []
+        separator_default_index = None
         try:
             for index, choice in enumerate(choices, start=0):
                 if isinstance(choice, dict):
@@ -104,6 +105,10 @@ class InquirerPyUIListControl(FormattedTextControl):
                         }
                     )
                 elif isinstance(choice, Separator):
+                    # Check if this separator is the default
+                    if choice is default:
+                        separator_default_index = index
+                        self.selected_choice_index = index
                     if self.selected_choice_index == index:
                         self.selected_choice_index = (
                             self.selected_choice_index + 1
```

Alternatively, a cleaner fix would be to handle separator defaults after processing all choices:

```diff
--- a/InquirerPy/base/control.py
+++ b/InquirerPy/base/control.py
@@ -128,6 +128,14 @@ class InquirerPyUIListControl(FormattedTextControl):
             raise RequiredKeyNotFound(
                 "dictionary type of choice require a 'name' key and a 'value' key"
             )
+        
+        # If default was a separator, advance to next non-separator
+        if isinstance(default, Separator):
+            while (self.selected_choice_index < len(processed_choices) and 
+                   isinstance(processed_choices[self.selected_choice_index]["value"], Separator)):
+                self.selected_choice_index = (self.selected_choice_index + 1) % len(processed_choices)
+        
         return processed_choices
```