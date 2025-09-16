# Bug Report: troposphere.codeconnections Title Validation Not Enforced

**Target**: `troposphere.codeconnections.Connection`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `Connection.to_dict()` method does not validate resource titles even when validation is enabled, allowing invalid CloudFormation resource names containing special characters to be generated.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.codeconnections import Connection
import re

@given(
    invalid_title=st.text(min_size=1, max_size=255).filter(
        lambda x: not re.match(r'^[a-zA-Z0-9]+$', x)
    ),
    connection_name=st.text(min_size=1, max_size=255)
)
def test_title_validation_enforced(invalid_title, connection_name):
    """Test that invalid titles are rejected during to_dict()"""
    conn = Connection(invalid_title, ConnectionName=connection_name)
    
    # This should raise ValueError for invalid title, but doesn't
    conn.to_dict(validation=True)
```

**Failing input**: `invalid_title='my-invalid-title!', connection_name='ValidName'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.codeconnections import Connection

conn = Connection("my-invalid-title!", ConnectionName="ValidConnectionName")
result = conn.to_dict(validation=True)

print(f"Invalid title accepted: {list(result.keys())}")

try:
    conn.validate_title()
except ValueError as e:
    print(f"validate_title() would catch it: {e}")
```

## Why This Is A Bug

CloudFormation resource names must be alphanumeric only (matching `^[a-zA-Z0-9]+$`). The `BaseAWSObject` class has a `validate_title()` method that enforces this requirement, but `to_dict(validation=True)` only calls `validate()` and `_validate_props()`, not `validate_title()`. This allows invalid resource names to pass through to CloudFormation templates, which will fail during stack creation.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -337,6 +337,7 @@ class BaseAWSObject:
     def to_dict(self, validation: bool = True) -> Dict[str, Any]:
         if validation and self.do_validation:
+            self.validate_title()
             self._validate_props()
             self.validate()
```