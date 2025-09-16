# Bug Report: troposphere.validators.boolean Case Sensitivity Inconsistency

**Target**: `troposphere.validators.boolean`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The boolean validator accepts "True" and "False" but rejects "TRUE" and "FALSE", showing inconsistent case handling.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import boolean

@given(st.sampled_from(["true", "false"]))
def test_boolean_validator_case_consistency(base_value):
    test_cases = [
        base_value.lower(),   # "true" or "false"
        base_value.upper(),   # "TRUE" or "FALSE"  
        base_value.capitalize(),  # "True" or "False"
    ]
    
    results = []
    for test_value in test_cases:
        try:
            result = boolean(test_value)
            results.append((test_value, "success", result))
        except ValueError:
            results.append((test_value, "error", None))
    
    success_count = sum(1 for _, status, _ in results if status == "success")
    
    if 0 < success_count < len(results):
        successes = [v for v, s, _ in results if s == "success"]
        failures = [v for v, s, _ in results if s == "error"]
        assert False, f"Boolean validator inconsistent: accepts {successes} but rejects {failures}"
```

**Failing input**: `base_value='true'`

## Reproducing the Bug

```python
from troposphere.validators import boolean

test_values = ["true", "True", "TRUE", "false", "False", "FALSE"]

for value in test_values:
    try:
        result = boolean(value)
        print(f"✓ boolean('{value}') = {result}")
    except ValueError:
        print(f"✗ boolean('{value}') raised ValueError")
```

## Why This Is A Bug

The validator accepts both lowercase ("true") and title case ("True") but rejects uppercase ("TRUE"). This inconsistency violates the principle of least surprise - if the validator is case-insensitive enough to accept "True", users would reasonably expect it to also accept "TRUE".

## Fix

```diff
def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x in [True, 1, "1", "true", "True", "TRUE"]:
        return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x in [False, 0, "0", "false", "False", "FALSE"]:
        return False
    raise ValueError
```