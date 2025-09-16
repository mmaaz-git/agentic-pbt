# Bug Report: troposphere.validators boolean() Accepts Floats 0.0 and 1.0

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `boolean()` validator incorrectly accepts float values 0.0 and 1.0, violating its documented contract that only specific boolean-like values should be accepted.

## Property-Based Test

```python
@given(st.data())
def test_boolean_validator_invalid_inputs(data):
    """Test that boolean validator rejects invalid inputs"""
    invalid = data.draw(st.one_of(
        st.integers().filter(lambda x: x not in [0, 1]),
        st.text().filter(lambda x: x not in ["0", "1", "true", "True", "false", "False"]),
        st.floats(),
        st.none(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    ))
    
    with pytest.raises(ValueError):
        validators.boolean(invalid)
```

**Failing input**: `0.0`

## Reproducing the Bug

```python
from troposphere import validators

result = validators.boolean(0.0)
print(f"validators.boolean(0.0) = {result}")

result = validators.boolean(1.0)
print(f"validators.boolean(1.0) = {result}")
```

## Why This Is A Bug

The boolean validator's type hints explicitly specify it should only accept `Literal[True, 1, "true", "True"]` or `Literal[False, 0, "false", "False"]`. Floats are not in this contract. The bug occurs because Python's equality operator treats `0.0 == 0` and `1.0 == 1` as True, causing the `in` operator check to incorrectly match float values.

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