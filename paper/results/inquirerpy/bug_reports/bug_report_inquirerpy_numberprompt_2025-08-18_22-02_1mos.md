# Bug Report: NumberPrompt Min/Max Bounds Not Enforced on Initialization

**Target**: `InquirerPy.prompts.NumberPrompt`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

NumberPrompt fails to enforce min_allowed and max_allowed bounds on the default value during initialization, causing the prompt to return 0.0 instead of the clamped value.

## Property-Based Test

```python
from hypothesis import assume, given, strategies as st
from InquirerPy.prompts import NumberPrompt
from decimal import Decimal

@given(
    min_val=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    max_val=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    default_val=st.floats(min_value=-1e9, max_value=1e9, allow_nan=False, allow_infinity=False),
)
def test_number_prompt_min_max_bounds(min_val, max_val, default_val):
    assume(min_val <= max_val)
    
    prompt = NumberPrompt(
        message="Test",
        min_allowed=min_val,
        max_allowed=max_val,
        default=default_val,
        float_allowed=True
    )
    
    value = prompt.value
    
    if min_val is not None:
        assert value >= Decimal(str(min_val))
    
    if max_val is not None:
        assert value <= Decimal(str(max_val))
```

**Failing input**: `min_val=1.0, max_val=10.0, default_val=0.0`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from InquirerPy.prompts import NumberPrompt

prompt = NumberPrompt(
    message="Test",
    min_allowed=1.0,
    max_allowed=10.0,
    default=0.0,
    float_allowed=True
)

print(f"Expected: value >= 1.0")
print(f"Actual: value = {prompt.value}")
```

## Why This Is A Bug

The NumberPrompt documentation and implementation clearly intends for min_allowed and max_allowed to constrain the value. The value.setter method (lines 596-604) enforces these bounds when the value is set, but the initialization path through _on_rendered (lines 343-368) bypasses this validation, setting buffer text directly without bounds checking. This violates the invariant that the prompt value should always be within the specified bounds.

## Fix

The _on_rendered method should clamp the default value to the min/max bounds before setting the buffer text:

```diff
--- a/InquirerPy/prompts/number.py
+++ b/InquirerPy/prompts/number.py
@@ -343,11 +343,18 @@ class NumberPrompt(BaseComplexPrompt):
     def _on_rendered(self, _) -> None:
         """Additional processing to adjust buffer content after render."""
         if self._no_default:
             return
+        
+        # Apply min/max bounds to default value
+        default = self._default
+        if self._min is not None:
+            default = max(default, self._min if not self._float else Decimal(str(self._min)))
+        if self._max is not None:
+            default = min(default, self._max if not self._float else Decimal(str(self._max)))
+        
         if not self._float:
-            self._whole_buffer.text = str(self._default)
+            self._whole_buffer.text = str(default)
             self._integral_buffer.text = "0"
         else:
-            if self._sn_pattern.match(str(self._default)) is None:
-                whole_buffer_text, integral_buffer_text = str(self._default).split(".")
+            if self._sn_pattern.match(str(default)) is None:
+                whole_buffer_text, integral_buffer_text = str(default).split(".")
             else:
-                whole_buffer_text, integral_buffer_text = self._fix_sn(str(self._default))
+                whole_buffer_text, integral_buffer_text = self._fix_sn(str(default))
```