# Bug Report: troposphere BaseAWSObject accepts empty string as title

**Target**: `troposphere.BaseAWSObject.validate_title`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The title validation accepts empty strings despite requiring alphanumeric characters, allowing creation of CloudFormation resources with invalid names.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import BaseAWSObject
import re

@given(st.text())
def test_title_validation(title):
    valid_names = re.compile(r"^[a-zA-Z0-9]+$")
    
    class TestResource(BaseAWSObject):
        resource_type = "Test::Resource"
        props = {}
    
    if title and valid_names.match(title):
        obj = TestResource(title=title, validation=True)
        assert obj.title == title
    else:
        with pytest.raises(ValueError, match='Name .* not alphanumeric'):
            TestResource(title=title, validation=True)
```

**Failing input**: `""`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import BaseAWSObject

class TestResource(BaseAWSObject):
    resource_type = "Test::Resource"
    props = {}

obj = TestResource(title="", validation=True)
print(f"Created resource with empty title: {obj.title}")
```

## Why This Is A Bug

The regex pattern `^[a-zA-Z0-9]+$` requires at least one alphanumeric character (the `+` quantifier), but the validation logic checks `if not self.title or not valid_names.match(self.title)`. When `self.title` is an empty string, the condition becomes `if not "" or ...`, which evaluates to `if True or ...`, short-circuiting and never checking the regex. This allows invalid empty resource names in CloudFormation templates.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -325,7 +325,7 @@ class BaseAWSObject:
         )
 
     def validate_title(self) -> None:
-        if not self.title or not valid_names.match(self.title):
+        if self.title is None or not valid_names.match(self.title):
             raise ValueError('Name "%s" not alphanumeric' % self.title)
 
     def validate(self) -> None:
```