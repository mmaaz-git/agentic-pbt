# Bug Report: troposphere BaseAWSObject ignores validation=False for title

**Target**: `troposphere.BaseAWSObject.__init__`
**Severity**: Medium  
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `validation=False` parameter is ignored for title validation, causing title validation to always run even when explicitly disabled.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import BaseAWSObject

@given(st.text(min_size=1).filter(lambda x: not x.isalnum()))
def test_validation_flag_skips_title(invalid_title):
    class TestResource(BaseAWSObject):
        resource_type = "Test::Resource"
        props = {}
    
    # With validation=False, should accept any title
    obj = TestResource(title=invalid_title, validation=False)
    assert obj.title == invalid_title
```

**Failing input**: `"test-with-dashes"`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import BaseAWSObject

class TestResource(BaseAWSObject):
    resource_type = "Test::Resource"
    props = {}

try:
    obj = TestResource(title="test-with-dashes", validation=False)
    print(f"Created resource: {obj.title}")
except ValueError as e:
    print(f"validation=False still raised: {e}")
```

## Why This Is A Bug

The `validation` parameter is stored in `self.do_validation` but title validation occurs before this flag is checked. The title is validated on line 184 unconditionally, while the `do_validation` flag is only used later during `to_dict()`. This defeats the purpose of the validation flag for users who need to work with non-standard naming temporarily.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -180,8 +180,9 @@ class BaseAWSObject:
         ]
 
         # try to validate the title if its there
-        if self.title:
-            self.validate_title()
+        if self.do_validation:
+            if self.title:
+                self.validate_title()
 
         # Create the list of properties set on this object by the user
         self.properties = {}
```