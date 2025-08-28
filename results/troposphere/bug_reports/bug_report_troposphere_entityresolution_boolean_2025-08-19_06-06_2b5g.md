# Bug Report: troposphere.entityresolution.boolean Accepts Float Values Inconsistently

**Target**: `troposphere.entityresolution.boolean`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `boolean()` function unexpectedly accepts float values 0.0 and 1.0, converting them to False and True respectively, while rejecting other float values like 2.0 or 0.5.

## Property-Based Test

```python
@given(st.one_of(
    st.integers(min_value=2, max_value=100),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=1).filter(lambda x: x not in ["true", "True", "false", "False", "1", "0"]),
    st.none(),
    st.lists(st.integers())
))
def test_invalid_inputs_raise_valueerror(x):
    """Test that invalid inputs raise ValueError."""
    try:
        result = er.boolean(x)
        assert False, f"boolean({repr(x)}) returned {result} but was expected to raise ValueError"
    except ValueError:
        pass  # Expected
```

**Failing input**: `0.0`

## Reproducing the Bug

```python
import troposphere.entityresolution as er

result1 = er.boolean(0.0)
print(f"boolean(0.0) = {result1}")  # False

result2 = er.boolean(1.0)
print(f"boolean(1.0) = {result2}")  # True

try:
    er.boolean(2.0)
except ValueError:
    print("boolean(2.0) raises ValueError")
```

## Why This Is A Bug

The function's implementation shows clear intent to accept only specific values: booleans, integers 0/1, and strings "0"/"1"/"true"/"false" with specific casing. Accepting floats 0.0 and 1.0 occurs due to Python's equality behavior (0.0 == 0 is True) when using the `in` operator with lists. This creates inconsistent behavior where some floats work but others don't.

## Fix

```diff
def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x is True or x == 1 and type(x) == int or x in ["1", "true", "True"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x is False or x == 0 and type(x) == int or x in ["0", "false", "False"]:
         return False
     raise ValueError
```