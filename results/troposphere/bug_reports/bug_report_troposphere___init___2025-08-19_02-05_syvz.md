# Bug Report: troposphere Empty String Title Validation Bypass

**Target**: `troposphere.BaseAWSObject.validate_title`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The title validation in troposphere's BaseAWSObject class fails to validate empty strings, allowing resources to be created with empty titles which should be invalid according to the alphanumeric validation rules.

## Property-Based Test

```python
def test_title_validation():
    """Resource titles should be alphanumeric only"""
    invalid_titles = ["", "My-Resource", "Test!"]
    for title in invalid_titles:
        try:
            instance = lightsail.Instance(
                title=title,
                BlueprintId="amazon_linux_2",
                BundleId="nano_2_0",
                InstanceName="test"
            )
            assert False, f"Should have raised for title: {title}"
        except ValueError:
            pass  # Expected
```

**Failing input**: `title=""`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.lightsail as lightsail

instance = lightsail.Instance(
    title="",  # Empty string should be invalid
    BlueprintId="amazon_linux_2",
    BundleId="nano_2_0",
    InstanceName="test"
)

print(f"Title: '{instance.title}'")  # Outputs: Title: ''
result = instance.to_dict()
print("Successfully created resource with empty title")
```

## Why This Is A Bug

The `validate_title()` method is designed to ensure titles are alphanumeric, rejecting empty strings and special characters. However, the validation is only triggered when the title is truthy (line 183 in `__init__.py`), meaning empty strings bypass validation entirely. This violates the intended contract that titles must match the regex `^[a-zA-Z0-9]+$`, which requires at least one alphanumeric character.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -180,8 +180,8 @@ class BaseAWSObject:
         ]
 
         # try to validate the title if its there
-        if self.title:
-            self.validate_title()
+        if self.title is not None:
+            self.validate_title()
 
         # Create the list of properties set on this object by the user
         self.properties = {}
```