# Bug Report: troposphere.healthimaging Empty/None Title Validation Bypass

**Target**: `troposphere.healthimaging.Datastore` 
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `Datastore` class accepts empty string and None as titles, bypassing validation and producing invalid CloudFormation references.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.healthimaging as healthimaging

invalid_titles = st.one_of(
    st.just(''),    # empty string
    st.just(None),  # None value
)

@given(invalid_titles)
def test_invalid_title_rejected(title):
    """Empty/None titles should raise ValueError"""
    try:
        healthimaging.Datastore(title)
        assert False, f"Title {repr(title)} should have been rejected"
    except ValueError:
        pass  # Expected
```

**Failing input**: `''` (empty string) and `None`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.healthimaging as healthimaging

# Empty string bypasses validation
ds1 = healthimaging.Datastore('')
print(f"Empty title accepted: {ds1.title!r}")
print(f"Invalid ref generated: {ds1.ref().to_dict()}")

# None also bypasses validation  
ds2 = healthimaging.Datastore(None)
print(f"None title accepted: {ds2.title!r}")
print(f"Invalid ref generated: {ds2.ref().to_dict()}")
```

## Why This Is A Bug

The validation code in `BaseAWSObject.__init__` only calls `validate_title()` when title is truthy:

```python
if self.title:
    self.validate_title()
```

This allows empty string and None to bypass validation, even though `validate_title()` is designed to reject them. The resulting CloudFormation references (`{'Ref': ''}` and `{'Ref': None}`) are invalid and would fail during stack creation.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -180,8 +180,9 @@ class BaseAWSObject:
         ]
 
         # try to validate the title if its there
-        if self.title:
-            self.validate_title()
+        # Validate title even if empty/None to catch invalid values
+        if self.title is not None:
+            self.validate_title()
 
         # Create the list of properties set on this object by the user
         self.properties = {}
```