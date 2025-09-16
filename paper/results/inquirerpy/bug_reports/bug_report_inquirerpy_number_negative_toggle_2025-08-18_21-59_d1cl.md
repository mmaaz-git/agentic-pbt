# Bug Report: InquirerPy.NumberPrompt Negative Toggle Fails for Zero

**Target**: `InquirerPy.prompts.number.NumberPrompt`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

NumberPrompt's negative toggle functionality fails to negate the value "0", breaking the idempotence property where toggling negative twice should return to the original value.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from InquirerPy.prompts.number import NumberPrompt

@given(initial_val=st.integers(min_value=0, max_value=1000))
def test_number_prompt_negative_toggle_idempotence(initial_val):
    prompt = NumberPrompt(message="Test", default=initial_val)
    
    prompt._whole_buffer.text = str(initial_val)
    original = prompt._whole_buffer.text
    
    prompt._handle_negative_toggle(None)
    assert prompt._whole_buffer.text == f"-{original}"
    
    prompt._handle_negative_toggle(None)
    assert prompt._whole_buffer.text == original
```

**Failing input**: `initial_val=0`

## Reproducing the Bug

```python
from InquirerPy.prompts.number import NumberPrompt

prompt = NumberPrompt(message="Test", default=0)
prompt._whole_buffer.text = "0"

print(f"Initial: '{prompt._whole_buffer.text}'")
prompt._handle_negative_toggle(None)
print(f"After toggle: '{prompt._whole_buffer.text}'")
print(f"Expected: '-0', Got: '{prompt._whole_buffer.text}'")
```

## Why This Is A Bug

The negative toggle should work consistently for all numeric values. While "-0" and "0" are mathematically equivalent, the UI behavior should be consistent - if a user toggles negative on "0", they expect to see "-0", and toggling again should return to "0". This breaks the idempotence property and creates inconsistent UX.

## Fix

The issue occurs because the code doesn't explicitly handle the case where the buffer text is "0". The fix requires special handling for this edge case:

```diff
--- a/InquirerPy/prompts/number.py
+++ b/InquirerPy/prompts/number.py
@@ -509,6 +509,9 @@ class NumberPrompt(BaseComplexPrompt):
         if self._whole_buffer.text == "-":
             self._whole_buffer.text = "0"
             return
+        if self._whole_buffer.text == "0":
+            self._whole_buffer.text = "-0"
+            return
         if self._whole_buffer.text.startswith("-"):
             move_cursor = self._whole_buffer.cursor_position < len(
                 self._whole_buffer.text
```