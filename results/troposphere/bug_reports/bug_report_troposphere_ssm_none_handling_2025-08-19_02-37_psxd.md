# Bug Report: troposphere.validators.ssm None Value Handling

**Target**: `troposphere.validators.ssm.validate_document_content`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `validate_document_content` function crashes with `TypeError` when given `None` as input, instead of gracefully handling it and raising the expected `ValueError`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.validators.ssm as ssm_validators

@given(st.one_of(st.none(), st.integers(), st.floats(), st.lists(st.integers())))
def test_validate_document_content_invalid_types(value):
    """Test that non-dict, non-string types are rejected"""
    if isinstance(value, dict):
        return  # Skip dicts, they're valid
    
    try:
        result = ssm_validators.validate_document_content(value)
        assert False, f"Should have rejected non-dict/non-string type: {type(value)}"
    except (ValueError, TypeError) as e:
        # Should raise an error for invalid types
        pass
```

**Failing input**: `None`

## Reproducing the Bug

```python
import troposphere.validators.ssm as ssm_validators

result = ssm_validators.validate_document_content(None)
```

## Why This Is A Bug

The function should validate whether content is a dict, JSON string, or YAML string, and raise a `ValueError` with message "Content must be one of dict or json/yaml string" for invalid inputs. However, when given `None`, the function passes it to `json.loads()` which raises `TypeError: the JSON object must be str, bytes or bytearray, not NoneType`. This inconsistent error handling makes the function's behavior unpredictable and violates its error contract.

## Fix

```diff
--- a/troposphere/validators/ssm.py
+++ b/troposphere/validators/ssm.py
@@ -14,10 +14,13 @@ def validate_document_content(x):
     """
 
     def check_json(x):
         import json
 
+        if not isinstance(x, (str, bytes, bytearray)):
+            return False
+
         try:
             json.loads(x)
             return True
         except json.decoder.JSONDecodeError:
             return False
```