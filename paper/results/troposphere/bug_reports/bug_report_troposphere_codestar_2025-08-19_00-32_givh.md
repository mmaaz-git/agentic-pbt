# Bug Report: troposphere.validators Boolean Validator Incorrectly Accepts Float Values

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `boolean` validator function incorrectly accepts float values `0.0` and `1.0` as valid boolean representations due to Python's numeric equality behavior, violating its intended type contract.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import validators

@given(
    invalid_value=st.one_of(
        st.text(min_size=1).filter(lambda x: x not in ["true", "True", "false", "False", "0", "1"]),
        st.integers(min_value=2),
        st.floats(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.text())
    )
)
def test_boolean_validator_rejects_invalid(invalid_value):
    """Test that boolean validator rejects invalid values."""
    try:
        validators.boolean(invalid_value)
        assert False, f"Should have rejected {invalid_value!r}"
    except ValueError:
        pass  # Expected
```

**Failing input**: `0.0`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import validators

result = validators.boolean(0.0)
print(f"validators.boolean(0.0) = {result}")  # Returns False, should raise ValueError

result = validators.boolean(1.0)  
print(f"validators.boolean(1.0) = {result}")  # Returns True, should raise ValueError
```

## Why This Is A Bug

The boolean validator is intended to strictly validate boolean-like inputs for CloudFormation templates. The current implementation uses `x in [0, 1, ...]` which unintentionally accepts float values due to Python's equality behavior (`0.0 == 0` is True). This violates the function's type contract and could lead to:

1. Type confusion when float calculations accidentally pass as booleans
2. Inconsistent validation (accepts 0.0/1.0 but rejects 0.5)
3. Silent acceptance of incorrect types in CloudFormation resources

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -36,9 +36,11 @@ def boolean(x: Literal[False, 0, "false", "False"]) -> Literal[False]: ...
 
 
 def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x is True or x in ["1", "true", "True"]:
+        return True
+    if (isinstance(x, int) and not isinstance(x, bool) and x == 1):
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x is False or x in ["0", "false", "False"] or (isinstance(x, int) and not isinstance(x, bool) and x == 0):
         return False
     raise ValueError
```