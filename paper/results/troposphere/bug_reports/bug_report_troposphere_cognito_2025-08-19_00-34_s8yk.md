# Bug Report: troposphere.cognito Title Validation Bypass

**Target**: `troposphere.cognito` (affects all AWSObject subclasses)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

AWSObject classes in troposphere.cognito (and likely all troposphere modules) incorrectly accept empty string and None as titles, bypassing alphanumeric validation that should reject these values.

## Property-Based Test

```python
from hypothesis import given, strategies as st, example
import pytest

def invalid_title_strategy():
    return st.text(min_size=1, max_size=50).filter(
        lambda s: not re.match(r'^[a-zA-Z0-9]+$', s) and s != ""
    )

@given(title=invalid_title_strategy())
@example(title="")  # Empty string should be invalid
def test_invalid_titles_rejected(title):
    """Non-alphanumeric titles should raise ValueError."""
    with pytest.raises(ValueError, match="not alphanumeric"):
        cognito.IdentityPool(
            title=title,
            AllowUnauthenticatedIdentities=True
        )
```

**Failing input**: `""`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import cognito, Template

# Bug: Empty title is accepted during creation
pool = cognito.IdentityPool(
    title="",
    AllowUnauthenticatedIdentities=True
)
print(f"Created pool with empty title: '{pool.title}'")

# But validate_title() would reject it
try:
    pool.validate_title()
except ValueError as e:
    print(f"Direct validation fails: {e}")

# This creates malformed CloudFormation templates
template = Template()
template.add_resource(pool)
print(f"Template resources: {list(template.resources.keys())}")  # Shows ['']
```

## Why This Is A Bug

The title validation logic is inconsistent:
1. `__init__` only calls `validate_title()` if title is truthy (`if self.title:`)
2. But `validate_title()` checks `if not self.title or not valid_names.match(self.title)`
3. This allows empty/None titles to bypass validation, creating CloudFormation resources without valid logical names
4. The docstring and regex pattern clearly indicate titles must be alphanumeric, but empty/None violate this contract

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -234,8 +234,7 @@ class BaseAWSObject(object):
         ]
 
         # try to validate the title if its there
-        if self.title:
-            self.validate_title()
+        self.validate_title()
 
         # Create the list of properties set on this object by the user
         self.properties = {}
@@ -363,7 +362,7 @@ class BaseAWSObject(object):
         return self.to_json()
 
     def validate_title(self) -> None:
-        if not self.title or not valid_names.match(self.title):
+        if self.title is not None and (not self.title or not valid_names.match(self.title)):
             raise ValueError('Name "%s" not alphanumeric' % self.title)
```

Note: The fix needs careful consideration as it may break existing code that relies on None titles for certain use cases.