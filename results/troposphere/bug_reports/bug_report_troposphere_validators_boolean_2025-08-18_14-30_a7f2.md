# Bug Report: troposphere.validators Boolean Validator Accepts Floats

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `boolean` validator function incorrectly accepts float values 0.0 and 1.0, despite the function's documentation and implementation clearly listing only specific accepted values that do not include floats.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import boolean

@given(
    value=st.one_of(
        st.floats(),
        st.lists(st.integers())
    )
)
def test_boolean_validator_invalid_inputs(value):
    """Test that boolean validator rejects invalid inputs."""
    try:
        boolean(value)
        assert False, f"Expected ValueError for input {value}"
    except ValueError:
        pass  # Expected
```

**Failing input**: `0.0`

## Reproducing the Bug

```python
from troposphere.validators import boolean

result = boolean(0.0)
print(f"boolean(0.0) = {result}")  # Returns False, should raise ValueError

result = boolean(1.0)  
print(f"boolean(1.0) = {result}")  # Returns True, should raise ValueError
```

## Why This Is A Bug

The `boolean` function's implementation explicitly checks for specific values:
- True values: `True, 1, "1", "true", "True"`
- False values: `False, 0, "0", "false", "False"`

Float values like `0.0` and `1.0` are not in these lists and should raise `ValueError`. However, the comparison `x in [False, 0, "0", "false", "False"]` returns `True` for `0.0` because Python considers `0.0 == 0` to be `True`, despite them being different types.

## Fix

```diff
 def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x is True or (isinstance(x, int) and x == 1) or x in ["1", "true", "True"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x is False or (isinstance(x, int) and x == 0) or x in ["0", "false", "False"]:
         return False
     raise ValueError
```