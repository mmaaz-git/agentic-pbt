# Bug Report: troposphere Empty String Title Validation

**Target**: `troposphere.BaseAWSObject.__init__`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Empty string titles are incorrectly accepted as valid for AWS objects, violating the alphanumeric validation requirement.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import appsync

@given(st.just(""))
def test_aws_object_empty_title_validation(title):
    try:
        obj = appsync.Api(title, Name="TestApi")
        assert title.isalnum() or title is None
    except ValueError as e:
        assert "not alphanumeric" in str(e)
        if title:
            assert not title.isalnum()
```

**Failing input**: `""`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import appsync

api = appsync.Api("", Name="TestApi")
print(f"Created Api with empty title: '{api.title}'")
print(f"Empty string is alphanumeric: {''.isalnum()}")
```

## Why This Is A Bug

The validation logic requires titles to be alphanumeric. An empty string is not alphanumeric (`"".isalnum()` returns `False`), yet it's accepted as valid. The validation is skipped because the check `if self.title:` in `__init__` prevents `validate_title()` from being called when title is an empty string.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -180,8 +180,8 @@ class BaseAWSObject:
         ]
 
         # try to validate the title if its there
-        if self.title:
+        if self.title is not None:
             self.validate_title()
 
         # Create the list of properties set on this object by the user
```