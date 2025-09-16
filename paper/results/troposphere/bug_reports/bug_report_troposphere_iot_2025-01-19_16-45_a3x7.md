# Bug Report: troposphere.iot Empty Title Validation Bypass

**Target**: `troposphere.iot` (all troposphere AWS resources)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-01-19

## Summary

Resources in troposphere can be created with empty string or None titles, bypassing the alphanumeric validation that should reject them. The validation regex requires at least one alphanumeric character, but validation is skipped entirely for falsy titles.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.iot as iot
import pytest

@given(title=st.sampled_from(["", None]))
def test_empty_titles_should_be_rejected(title):
    """Empty and None titles should be rejected by validation"""
    with pytest.raises(ValueError, match="not alphanumeric"):
        iot.Certificate(title=title, Status="ACTIVE")
```

**Failing input**: `""`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.iot as iot

# Bug: Empty title bypasses validation
cert = iot.Certificate(title="", Status="ACTIVE")
print(f"Created Certificate with empty title: '{cert.title}'")

# Bug: None title also bypasses validation  
cert2 = iot.Certificate(title=None, Status="ACTIVE")
print(f"Created Certificate with None title: {cert2.title}")
```

## Why This Is A Bug

The `validate_title()` method checks that titles match `^[a-zA-Z0-9]+$`, which requires at least one alphanumeric character. Empty strings and None don't match this pattern but are accepted because validation is conditionally skipped:

```python
# In BaseAWSObject.__init__:
if self.title:
    self.validate_title()
```

This means validation only runs for truthy titles, allowing invalid empty/None titles to bypass the check entirely. The docstring and regex clearly indicate all titles should be alphanumeric, making this a contract violation.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -180,8 +180,7 @@ class BaseAWSObject:
         ]
 
         # try to validate the title if its there
-        if self.title:
-            self.validate_title()
+        self.validate_title()
 
         # Create the list of properties set on this object by the user
         self.properties = {}
```