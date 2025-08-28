# Bug Report: troposphere.validators.boolean Raises ValueError Without Message

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `boolean` validator in troposphere raises a bare `ValueError` without any error message when given invalid input, making debugging difficult and inconsistent with other validators like `integer`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.kinesisanalyticsv2 as kinesisanalyticsv2

@given(invalid_value=st.one_of(
    st.integers(),
    st.floats(),
    st.text(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text())
).filter(lambda x: not isinstance(x, bool) and x not in [0, 1]))
def test_application_snapshot_configuration_invalid_type(invalid_value):
    config = kinesisanalyticsv2.ApplicationSnapshotConfiguration(
        SnapshotsEnabled=invalid_value
    )
    dict_repr = config.to_dict()  # Raises ValueError with no message
```

**Failing input**: `-1`

## Reproducing the Bug

```python
from troposphere.validators import boolean

try:
    boolean(-1)
except ValueError as e:
    print(f"Error message: '{e}'")  # Prints: Error message: ''
    print(f"Args: {e.args}")         # Prints: Args: ()
```

## Why This Is A Bug

The boolean validator violates the established pattern in troposphere validators. The integer validator provides helpful error messages like `'not_a_number' is not a valid integer`, but the boolean validator raises a bare exception. This makes debugging difficult for users who don't understand why their boolean property is failing validation.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -40,7 +40,7 @@ def boolean(x: Any) -> bool:
         return True
     if x in [False, 0, "0", "false", "False"]:
         return False
-    raise ValueError
+    raise ValueError("%r is not a valid boolean" % x)
 
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
```