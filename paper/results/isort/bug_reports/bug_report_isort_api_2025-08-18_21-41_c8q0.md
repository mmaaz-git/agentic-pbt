# Bug Report: isort.api Check-Sort Inconsistency with Trailing Newlines

**Target**: `isort.api.check_code_string` and `isort.api.sort_code_string`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `check_code_string` function returns True indicating code is properly sorted, but `sort_code_string` still modifies the code by adding a trailing newline, violating the expected contract between these functions.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from isort.api import check_code_string, sort_code_string

@given(st.text())
def test_check_sort_consistency(code):
    sorted_code = sort_code_string(code)
    
    if check_code_string(code):
        assert code == sorted_code, "check returned True but sort changed the code"
```

**Failing input**: `"import a\nimport b"` (without trailing newline)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort.api import check_code_string, sort_code_string

code = "import a\nimport b"

is_sorted = check_code_string(code)
print(f"check_code_string: {is_sorted}")

sorted_code = sort_code_string(code)
print(f"Original: {repr(code)}")
print(f"Sorted:   {repr(sorted_code)}")

if is_sorted:
    assert code == sorted_code, "check says sorted but sort modifies it!"
```

## Why This Is A Bug

The contract between `check_code_string` and `sort_code_string` should be:
- If `check_code_string(code)` returns True, then `sort_code_string(code) == code`
- If code needs modification, `check_code_string` should return False

This inconsistency breaks workflows where users check if sorting is needed before applying it. Users may skip sorting based on the check result, leading to inconsistent formatting.

## Fix

Either:
1. `check_code_string` should return False when trailing newline is missing, or
2. `sort_code_string` should not add trailing newlines when the original code doesn't have them

Option 2 is likely preferable to maintain backward compatibility. The issue appears to be that isort always adds a trailing newline to ensure proper file formatting, but this behavior should be consistent between check and sort operations.