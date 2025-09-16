# Bug Report: troposphere.launchwizard Unicode Title Validation Inconsistency

**Target**: `troposphere.launchwizard.Deployment`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `validate_title()` method rejects Unicode alphanumeric characters with error message "not alphanumeric", even though Python's `isalnum()` returns `True` for these characters, creating a misleading API contract.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import launchwizard

unicode_alphanumeric = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
    min_size=1,
    max_size=50
).filter(lambda x: x.isalnum() and not x.isascii())

@given(title=unicode_alphanumeric)
def test_unicode_title_inconsistency(title):
    assert title.isalnum()  # Python says it's alphanumeric
    
    try:
        deployment = launchwizard.Deployment(
            title,
            DeploymentPatternName="pattern",
            Name="name",
            WorkloadName="workload"
        )
        assert False, f"Expected ValueError for '{title}'"
    except ValueError as e:
        assert 'not alphanumeric' in str(e)  # But error says it's not
```

**Failing input**: `'µ'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import launchwizard

title = 'µ'
print(f"Python isalnum(): {title.isalnum()}")  # True

deployment = launchwizard.Deployment(
    title,
    DeploymentPatternName="pattern",
    Name="name",
    WorkloadName="workload"
)
```

## Why This Is A Bug

The validation uses regex `^[a-zA-Z0-9]+$` which only accepts ASCII alphanumeric characters, but the error message says "not alphanumeric". Since Python's `isalnum()` returns `True` for Unicode letters like 'µ', 'Ω', 'ñ', etc., the error message is misleading. Users would reasonably expect Unicode support or at least a clearer error message like "only ASCII alphanumeric characters allowed".

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -325,7 +325,7 @@ class BaseAWSObject:
 
     def validate_title(self) -> None:
         if not self.title or not valid_names.match(self.title):
-            raise ValueError('Name "%s" not alphanumeric' % self.title)
+            raise ValueError('Name "%s" must contain only ASCII alphanumeric characters (a-z, A-Z, 0-9)' % self.title)
```