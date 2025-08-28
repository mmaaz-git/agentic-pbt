# Bug Report: InquirerPy.NumberPrompt Float Min/Max Constraints Not Enforced

**Target**: `InquirerPy.prompts.number.NumberPrompt`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

NumberPrompt fails to enforce min_allowed and max_allowed constraints when float_allowed=True, resulting in values outside the specified bounds.

## Property-Based Test

```python
from decimal import Decimal
from hypothesis import given, strategies as st, assume
from InquirerPy.prompts.number import NumberPrompt

@given(
    min_val=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    max_val=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    test_val=st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
)
def test_number_prompt_float_min_max_constraints(min_val, max_val, test_val):
    assume(min_val <= max_val)
    
    prompt = NumberPrompt(
        message="Test",
        float_allowed=True,
        min_allowed=min_val,
        max_allowed=max_val,
        default=min_val
    )
    
    prompt.value = Decimal(str(test_val))
    
    assert prompt.value >= Decimal(str(min_val))
    assert prompt.value <= Decimal(str(max_val))
```

**Failing input**: `min_val=1.0, max_val=10.0, test_val=0.0`

## Reproducing the Bug

```python
from decimal import Decimal
from InquirerPy.prompts.number import NumberPrompt

prompt = NumberPrompt(
    message="Test",
    float_allowed=True,
    min_allowed=1.0,
    max_allowed=10.0,
    default=1.0
)

prompt.value = Decimal("0.0")
print(f"Value after setting to 0.0: {prompt.value}")
print(f"Expected: 1.0 (clamped to min), Got: {prompt.value}")
```

## Why This Is A Bug

The NumberPrompt documentation and code (lines 597-604 in number.py) clearly intend to clamp values to min_allowed and max_allowed bounds. The value setter correctly calculates the clamped value, but when float_allowed=True, it fails to update the buffers due to conditional checks on lines 613-616 that only update non-empty buffers.

## Fix

```diff
--- a/InquirerPy/prompts/number.py
+++ b/InquirerPy/prompts/number.py
@@ -610,10 +610,8 @@ class NumberPrompt(BaseComplexPrompt):
             else:
                 whole_buffer_text, integral_buffer_text = self._fix_sn(str(value))
 
-            if self._whole_buffer.text:
-                self._whole_buffer.text = whole_buffer_text
-            if self._integral_buffer.text:
-                self._integral_buffer.text = integral_buffer_text
+            self._whole_buffer.text = whole_buffer_text
+            self._integral_buffer.text = integral_buffer_text
```