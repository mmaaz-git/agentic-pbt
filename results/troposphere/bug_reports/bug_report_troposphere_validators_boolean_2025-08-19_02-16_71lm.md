# Bug Report: troposphere.validators.boolean Accepts Undocumented Float Values

**Target**: `troposphere.validators.boolean`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `boolean` validator function accepts float values 1.0 and 0.0, contradicting its type hints which specify only specific literal values should be accepted.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import boolean

@given(st.floats(allow_nan=False, allow_infinity=False))
def test_boolean_only_accepts_documented_types(x):
    """Test that boolean validator only accepts documented input types"""
    try:
        result = boolean(x)
        # According to type hints, floats should never be accepted
        # Only True, False, 1, 0, "true", "false", "True", "False", "1", "0"
        assert isinstance(x, (bool, int, str)), f"Float {x} unexpectedly accepted"
    except ValueError:
        pass  # Expected for invalid inputs
```

**Failing input**: `1.0` and `0.0`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere.validators import boolean

print(f"boolean(1.0) = {boolean(1.0)}")  # Returns True (unexpected)
print(f"boolean(0.0) = {boolean(0.0)}")  # Returns False (unexpected)
print(f"boolean(-0.0) = {boolean(-0.0)}")  # Returns False (unexpected)
```

## Why This Is A Bug

The function's type hints explicitly declare accepted types via `Literal` annotations, but the implementation uses Python's `in` operator which performs equality checks. Since `1.0 == 1` and `0.0 == 0` in Python, float values pass through validation despite not being documented as acceptable inputs. This violates the API contract specified by the type hints.

## Fix

```diff
def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if type(x) in (bool, int, str) and x in [True, 1, "1", "true", "True"]:
        return True
-    if x in [False, 0, "0", "false", "False"]:
+    if type(x) in (bool, int, str) and x in [False, 0, "0", "false", "False"]:
        return False
    raise ValueError
```