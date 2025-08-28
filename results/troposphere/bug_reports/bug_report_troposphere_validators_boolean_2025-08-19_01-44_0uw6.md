# Bug Report: troposphere.validators.boolean Accepts Float Values

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `boolean` validator function incorrectly accepts float values (0.0 and 1.0) when it should only accept bool, int, and specific string values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.validators import boolean

@given(st.one_of(
    st.integers(min_value=2),
    st.integers(max_value=-1),
    st.text(min_size=1).filter(lambda x: x not in ["true", "false", "True", "False", "1", "0"]),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
))
def test_boolean_validator_invalid(value):
    """Test that boolean validator rejects invalid inputs."""
    with pytest.raises(ValueError):
        boolean(value)
```

**Failing input**: `0.0`

## Reproducing the Bug

```python
from troposphere.validators import boolean

result = boolean(0.0)
print(f"boolean(0.0) = {result}")
print(f"Type: {type(result)}")

result2 = boolean(1.0)
print(f"boolean(1.0) = {result2}")
```

## Why This Is A Bug

The boolean validator is designed to accept only specific types and values as documented in the code:
- `True`, `False` (bool)
- `1`, `0` (int)
- `"1"`, `"0"`, `"true"`, `"false"`, `"True"`, `"False"` (str)

Accepting float values `0.0` and `1.0` violates this type contract. This could lead to unexpected behavior when users pass float values expecting them to be rejected, or when the validator is used in contexts where strict type checking is important.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -36,10 +36,10 @@ def boolean(x: Literal[False, 0, "false", "False"]) -> Literal[False]: ...
 
 
 def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x is True or x == 1 and isinstance(x, int) or x in ["1", "true", "True"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x is False or x == 0 and isinstance(x, int) or x in ["0", "false", "False"]:
         return False
     raise ValueError
```