# Bug Report: troposphere.eks Type Validation Issues

**Target**: `troposphere.eks`
**Severity**: Medium
**Bug Type**: Crash, Contract
**Date**: 2025-08-19

## Summary

The troposphere.eks module has multiple type validation issues: validator functions crash with TypeError on non-string inputs, and the Taint class allows invalid non-string types for its fields.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.eks as eks
import pytest

@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.none(),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text())
))
def test_validate_taint_key_non_string_types(value):
    try:
        result = eks.validate_taint_key(value)
    except TypeError as e:
        if "has no len()" in str(e):
            pytest.fail(f"validate_taint_key crashed with TypeError on {type(value).__name__} input: {e}")

@given(
    key=st.one_of(st.lists(st.text()), st.dictionaries(st.text(), st.text())),
    value=st.text(max_size=63),
    effect=st.sampled_from(eks.VALID_TAINT_EFFECT)
)
def test_taint_class_type_validation(key, value, effect):
    try:
        taint = eks.Taint(Key=key, Value=value, Effect=effect)
        if not isinstance(key, str):
            pytest.fail(f"Taint accepted non-string Key: {type(key).__name__}")
    except (ValueError, TypeError):
        pass
```

**Failing input**: `validate_taint_key(0)`, `validate_taint_value(0)`, `Taint(Key=[''], Value='', Effect='NO_EXECUTE')`

## Reproducing the Bug

```python
import troposphere.eks as eks

# Bug 1: validate_taint_key crashes on non-string input
try:
    eks.validate_taint_key(0)
except TypeError as e:
    print(f"validate_taint_key TypeError: {e}")

# Bug 2: validate_taint_value crashes on non-string input  
try:
    eks.validate_taint_value(0)
except TypeError as e:
    print(f"validate_taint_value TypeError: {e}")

# Bug 3: Taint class accepts invalid non-string types
taint = eks.Taint(Key=['test'], Value='value', Effect='NO_SCHEDULE')
print(f"Taint with list Key created: {taint.to_dict()}")
```

## Why This Is A Bug

1. **Validator Functions**: The `validate_taint_key` and `validate_taint_value` functions crash with unhelpful TypeErrors when given non-string inputs. They should either convert the input to string or raise a descriptive ValueError indicating that a string is required.

2. **Taint Class**: The Taint class allows lists and dictionaries to be passed as Key and Value fields, bypassing validation. This violates the AWS CloudFormation specification which requires these to be strings. The class should validate types before accepting them.

## Fix

```diff
--- a/troposphere/validators/eks.py
+++ b/troposphere/validators/eks.py
@@ -24,6 +24,10 @@ def validate_taint_key(taint_key):
     Taint Key validation rule.
     Property: Taint.Key
     """
+    if not isinstance(taint_key, str):
+        raise ValueError(
+            "Taint Key must be a string"
+        )
     if len(taint_key) < 1 or len(taint_key) > 63:
         raise ValueError(
             "Taint Key must be at least 1 character and maximum 63 characters"
@@ -36,6 +40,10 @@ def validate_taint_value(taint_value):
     Taint Value validation rule.
     Property: Taint.Value
     """
+    if not isinstance(taint_value, str):
+        raise ValueError(
+            "Taint Value must be a string"
+        )
     if len(taint_value) > 63:
         raise ValueError("Taint Value maximum characters is 63")
     return taint_value
```