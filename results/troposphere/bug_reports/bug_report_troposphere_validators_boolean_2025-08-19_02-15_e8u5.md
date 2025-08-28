# Bug Report: troposphere.validators.boolean Incorrectly Accepts Float Values

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The boolean validator incorrectly accepts float values 0.0 and 1.0, violating its documented contract of only accepting specific boolean-like values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere import validators

invalid_boolean_inputs = st.one_of(
    st.integers().filter(lambda x: x not in [0, 1]),
    st.text().filter(lambda x: x not in ['1', '0', 'true', 'false', 'True', 'False', '']),
    st.none(),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text())
)

@given(invalid_boolean_inputs)
def test_boolean_validator_rejects_invalid(value):
    """Test that boolean validator rejects invalid inputs."""
    with pytest.raises(ValueError):
        validators.boolean(value)
```

**Failing input**: `0.0`

## Reproducing the Bug

```python
from troposphere import validators

# Should raise ValueError but returns False
result = validators.boolean(0.0)
print(f"validators.boolean(0.0) = {result}")

# Also accepts 1.0
result = validators.boolean(1.0) 
print(f"validators.boolean(1.0) = {result}")
```

## Why This Is A Bug

The boolean validator is documented to accept only these values: `[True, False, 1, 0, '1', '0', 'true', 'false', 'True', 'False']`. However, it accepts `0.0` and `1.0` because Python's `in` operator uses `==` equality, where `0 == 0.0` and `1 == 1.0` evaluate to True. This violates the type contract and could lead to unexpected behavior when float values are passed where only specific boolean representations should be accepted.

## Fix

```diff
def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if type(x) in [bool, int, str] and x in [True, 1, "1", "true", "True"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if type(x) in [bool, int, str] and x in [False, 0, "0", "false", "False"]:
         return False
     raise ValueError
```