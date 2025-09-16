# Bug Report: troposphere.ecr Boolean Case Sensitivity Inconsistency

**Target**: `troposphere.ecr.boolean`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `boolean` function accepts mixed-case boolean strings ('true', 'True', 'false', 'False') but rejects all-uppercase variants ('TRUE', 'FALSE'), creating an inconsistent case-handling behavior.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.ecr as ecr
import pytest

@given(st.sampled_from(['true', 'True', 'false', 'False']))
def test_boolean_case_variations_should_work(base_value):
    upper_value = base_value.upper()
    try:
        result = ecr.boolean(upper_value)
        if base_value.lower() == 'true':
            assert result is True
        else:
            assert result is False
    except ValueError:
        pytest.fail(f"boolean() accepts '{base_value}' but rejects '{upper_value}'")
```

**Failing input**: `'true'` (which generates `'TRUE'` that gets rejected)

## Reproducing the Bug

```python
import troposphere.ecr as ecr

print(f"ecr.boolean('true') = {ecr.boolean('true')}")
print(f"ecr.boolean('True') = {ecr.boolean('True')}")

try:
    ecr.boolean('TRUE')
    print("ecr.boolean('TRUE') works")
except ValueError:
    print("ecr.boolean('TRUE') raises ValueError!")

print(f"ecr.boolean('false') = {ecr.boolean('false')}")  
print(f"ecr.boolean('False') = {ecr.boolean('False')}")

try:
    ecr.boolean('FALSE')
    print("ecr.boolean('FALSE') works")
except ValueError:
    print("ecr.boolean('FALSE') raises ValueError!")
```

## Why This Is A Bug

The function accepts both lowercase ('true') and mixed-case ('True') variants but arbitrarily rejects the all-uppercase variant ('TRUE'). This inconsistency violates the principle of least surprise and can cause issues when integrating with systems that use uppercase boolean strings (common in environment variables, configuration files, and various APIs).

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -38,10 +38,10 @@
 
 
 def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x in [True, 1, "1", "true", "True", "TRUE"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x in [False, 0, "0", "false", "False", "FALSE"]:
         return False
     raise ValueError
```