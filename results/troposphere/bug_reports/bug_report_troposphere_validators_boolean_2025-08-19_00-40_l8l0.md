# Bug Report: troposphere.validators.boolean Accepts Undocumented Float Values

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `boolean` validator function incorrectly accepts float values 0.0 and 1.0, returning False and True respectively, despite these types not being in the documented list of accepted values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import boolean

@given(x=st.one_of(
    st.integers().filter(lambda x: x not in [0, 1]),
    st.text().filter(lambda x: x not in ["0", "1", "true", "True", "false", "False"]),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text())
))
def test_boolean_validator_invalid_inputs(x):
    """Test that boolean validator raises ValueError for invalid inputs"""
    try:
        result = boolean(x)
        assert False, f"Expected ValueError for input {x!r}, but got {result!r}"
    except ValueError:
        pass  # Expected behavior
```

**Failing input**: `0.0`

## Reproducing the Bug

```python
from troposphere.validators import boolean

print(f"boolean(0.0) = {boolean(0.0)}")  # Returns False, should raise ValueError
print(f"boolean(1.0) = {boolean(1.0)}")  # Returns True, should raise ValueError
print(f"boolean(-0.0) = {boolean(-0.0)}")  # Returns False, should raise ValueError

try:
    boolean(0.5)  # Correctly raises ValueError
except ValueError:
    print("boolean(0.5) correctly raises ValueError")
```

## Why This Is A Bug

The boolean validator function explicitly lists accepted values: `[True, 1, "1", "true", "True"]` for True and `[False, 0, "0", "false", "False"]` for False. Float values are not in these lists but are accepted due to Python's equality comparison where `0.0 == 0` and `1.0 == 1` evaluate to True. This violates the function's type contract and allows unintended type coercion.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -36,9 +36,9 @@
 
 
 def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x is True or x == 1 and type(x) is int or x in ["1", "true", "True"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x is False or x == 0 and type(x) is int or x in ["0", "false", "False"]:
         return False
     raise ValueError
```