# Bug Report: isort.wrap_modes.from_string ValueError on Out-of-Range Integers

**Target**: `isort.wrap_modes.from_string`
**Severity**: Low
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `from_string` function in isort.wrap_modes raises a ValueError when given integer strings that are out of the valid WrapModes enum range (>=12), rather than gracefully handling invalid values.

## Property-Based Test

```python
@given(st.integers())
def test_from_string_with_integers(mode_int):
    # from_string should handle any integer string gracefully
    try:
        mode = wrap_modes.from_string(str(mode_int))
        # Should either return a valid mode or handle gracefully
        assert isinstance(mode, wrap_modes.WrapModes)
    except ValueError:
        # Should not crash for any integer input
        assert False, f"from_string crashed on integer {mode_int}"
```

**Failing input**: `mode_int=12` (or any integer >= 12)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages")
import isort.wrap_modes as wrap_modes

# Works fine for valid range (0-11)
mode = wrap_modes.from_string("11")
print(f"from_string('11'): {mode}")

# Crashes for out-of-range values
try:
    mode = wrap_modes.from_string("12")
    print(f"from_string('12'): {mode}")
except ValueError as e:
    print(f"from_string('12') raised ValueError: {e}")

try:
    mode = wrap_modes.from_string("100")
    print(f"from_string('100'): {mode}")
except ValueError as e:
    print(f"from_string('100') raised ValueError: {e}")
```

## Why This Is A Bug

The function attempts to convert any unrecognized string to an integer and pass it to the WrapModes enum constructor, which raises a ValueError for out-of-range values. This violates the principle of graceful degradation - the function should either return a default value or raise a more specific/informative error for invalid inputs. The current behavior could cause unexpected crashes in code that processes user input or configuration values.

## Fix

```diff
--- a/isort/wrap_modes.py
+++ b/isort/wrap_modes.py
@@ -11,7 +11,11 @@
 
 def from_string(value: str) -> "WrapModes":
-    return getattr(WrapModes, str(value), None) or WrapModes(int(value))
+    mode = getattr(WrapModes, str(value), None)
+    if mode is not None:
+        return mode
+    try:
+        return WrapModes(int(value))
+    except (ValueError, TypeError):
+        # Return default mode for invalid values
+        return WrapModes.GRID
```