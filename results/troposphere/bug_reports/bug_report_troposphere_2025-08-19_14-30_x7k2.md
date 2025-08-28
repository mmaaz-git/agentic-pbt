# Bug Report: Troposphere Empty Title Validation Bypass

**Target**: `troposphere.BaseAWSObject`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The BaseAWSObject class in troposphere fails to validate empty string titles, allowing creation of CloudFormation resources with invalid empty logical names.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import Parameter, valid_names

@given(title=st.text(min_size=0, max_size=300))
def test_parameter_title_validation(title):
    """Test Parameter title validation rules."""
    is_valid = (
        len(title) > 0 and 
        len(title) <= 255 and 
        valid_names.match(title) is not None
    )
    
    if is_valid:
        param = Parameter(title, Type="String")
        assert param.title == title
    else:
        try:
            param = Parameter(title, Type="String")
            assert False, f"Should have raised ValueError for invalid title: {title}"
        except ValueError:
            pass  # Expected
```

**Failing input**: `title=""`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import Parameter, Template

# Create parameter with empty title - should fail but doesn't
param = Parameter("", Type="String", Default="test")
print(f"Created Parameter with empty title: '{param.title}'")

# Add to template
template = Template()
template.add_parameter(param)

# Generate invalid CloudFormation JSON
print(template.to_json())
# Output shows invalid JSON with empty key:
# {
#  "Parameters": {
#   "": {
#    "Default": "test",
#    "Type": "String"
#   }
#  },
#  "Resources": {}
# }
```

## Why This Is A Bug

The BaseAWSObject.validate_title() method correctly rejects empty titles when called directly, but the validation is bypassed during object initialization. The __init__ method at lines 183-184 contains:

```python
if self.title:
    self.validate_title()
```

Since empty strings are falsy in Python, `if self.title:` evaluates to False when title is "", preventing validate_title() from being called. This allows creation of CloudFormation templates with empty logical names, which are invalid and will be rejected by AWS CloudFormation.

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
         self.properties = {}
```