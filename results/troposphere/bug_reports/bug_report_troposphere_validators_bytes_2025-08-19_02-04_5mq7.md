# Bug Report: troposphere.validators Integer and Double Validators Accept Bytes

**Target**: `troposphere.validators.integer` and `troposphere.validators.double`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `integer()` and `double()` validators in troposphere incorrectly accept bytes objects, which causes JSON serialization failures when creating CloudFormation templates.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import validators

@given(st.binary())
def test_integer_validator_bytes(value):
    """Test if integer validator incorrectly accepts bytes"""
    try:
        result = validators.integer(value)
        # If bytes are accepted and can be converted to int, that's a bug
        int(result)
        assert False, f"Integer validator should not accept bytes: {value!r}"
    except (ValueError, TypeError):
        pass  # Expected behavior
```

**Failing input**: `b'123'`, `b'0'`, `b'-5'`, etc.

## Reproducing the Bug

```python
import sys
import json
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators
from troposphere.medialive import Ac3Settings

# Bug 1: Validators accept bytes
result = validators.integer(b'42')
print(f"validators.integer(b'42') = {result!r}")  # Returns b'42'
print(f"type(result) = {type(result)}")           # <class 'bytes'>

# Bug 2: This breaks JSON serialization
settings = Ac3Settings()
settings.Dialnorm = b'10'  # bytes accepted due to validator bug
settings.Bitrate = b'128.5'

d = settings.to_dict()
print(f"to_dict() result: {d}")  # {'Dialnorm': b'10', 'Bitrate': b'128.5'}

try:
    json.dumps(d)
except TypeError as e:
    print(f"JSON serialization fails: {e}")
    # Output: Object of type bytes is not JSON serializable
```

## Why This Is A Bug

The validators are designed to validate CloudFormation property types. CloudFormation templates must be JSON-serializable, but bytes objects cannot be serialized to JSON. This violates the contract that validated values should be suitable for CloudFormation templates.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,6 +45,8 @@ def boolean(x: Any) -> bool:
 
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
+    if isinstance(x, bytes):
+        raise ValueError("%r bytes are not a valid integer type" % x)
     try:
         int(x)
     except (ValueError, TypeError):
@@ -92,6 +94,8 @@ def integer_list_item_checker(
 
 
 def double(x: Any) -> Union[SupportsFloat, SupportsIndex, str, bytes, bytearray]:
+    if isinstance(x, (bytes, bytearray)):
+        raise ValueError("%r bytes/bytearray are not a valid double type" % x)
     try:
         float(x)
     except (ValueError, TypeError):
```