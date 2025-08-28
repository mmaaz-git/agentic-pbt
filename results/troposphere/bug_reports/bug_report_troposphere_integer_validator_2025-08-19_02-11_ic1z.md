# Bug Report: troposphere.validators.integer Accepts Float Values

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The integer validator incorrectly accepts float values, including non-integer floats like 0.5, when it should only accept integers and string representations of integers.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest

@given(st.floats().filter(lambda x: not x.is_integer()))
def test_integer_validator_rejects_non_integer_floats(value):
    """Test that integer validator rejects non-integer float inputs"""
    from troposphere.validators import integer
    
    # Integer validator should reject non-integer floats
    with pytest.raises(ValueError):
        integer(value)
```

**Failing input**: `0.5`, `1.5`, `2.7`, etc.

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer

print(f"integer(0.5) = {integer(0.5)}")    # Returns 0.5, should raise ValueError
print(f"integer(1.5) = {integer(1.5)}")    # Returns 1.5, should raise ValueError
print(f"integer(2.7) = {integer(2.7)}")    # Returns 2.7, should raise ValueError
print(f"int(0.5) = {int(0.5)}")            # Python's int() truncates to 0
```

## Why This Is A Bug

The integer validator is designed to ensure values can be safely converted to integers. However, its implementation only checks if `int(x)` doesn't raise an exception, without verifying that the value is actually an integer. Python's `int()` function truncates float values rather than rejecting them, so `int(0.5)` returns `0` without error.

This violates the validator's contract - it should only accept actual integers or string representations of integers, not float values that lose precision when converted. The validator is used across 159 modules in troposphere for integer properties like memory sizes, port numbers, and counts. Accepting floats could lead to unexpected truncation and incorrect CloudFormation templates.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,6 +45,10 @@ def boolean(x: Any) -> bool:
 
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
+    # Reject float types (including float subclasses) unless they represent exact integers
+    if isinstance(x, float) and not isinstance(x, bool):
+        if not x.is_integer():
+            raise ValueError("%r is not a valid integer" % x)
     try:
         int(x)
     except (ValueError, TypeError):
```