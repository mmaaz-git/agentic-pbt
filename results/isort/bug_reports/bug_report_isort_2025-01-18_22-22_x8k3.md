# Bug Report: isort Check-Sort Inconsistency with Trailing Newlines

**Target**: `isort` (specifically `isort.check_code` and `isort.code`)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-01-18

## Summary

`isort.check_code()` returns `True` (indicating code is properly sorted) but `isort.code()` still modifies the code by adding a trailing newline, violating the expected contract between check and sort operations.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import isort

@given(st.text(min_size=0, max_size=100))
def test_check_sort_consistency(code):
    """If check_code returns True, then sort_code should return the same code."""
    try:
        if isort.check_code(code):
            sorted_code = isort.code(code)
            assert code == sorted_code, \
                f"check_code returned True but sort_code changed the code"
    except (isort.exceptions.FileSkipComment, isort.exceptions.FileSkipSetting):
        pass
```

**Failing input**: `"import a"` (any import statement without trailing newline)

## Reproducing the Bug

```python
import isort

code = "import a"

is_sorted = isort.check_code(code)
print(f"check_code result: {is_sorted}")  # True

sorted_code = isort.code(code)
print(f"Original: {repr(code)}")          # 'import a'
print(f"Sorted:   {repr(sorted_code)}")   # 'import a\n'
print(f"Equal? {code == sorted_code}")    # False

assert not (is_sorted and code != sorted_code), \
    "BUG: check_code returns True but sort_code modifies the code!"
```

## Why This Is A Bug

This violates the expected contract between `check_code` and `sort_code`:
- If `check_code` returns `True`, it indicates the code is already properly formatted
- Therefore, `sort_code` should return the identical code without modifications
- However, `sort_code` adds a trailing newline even when `check_code` says no changes are needed

This inconsistency can cause issues in:
- CI/CD pipelines that check formatting before applying it
- Editor integrations that rely on the check operation to determine if formatting is needed
- Any workflow that assumes `check_code() == True` means `sort_code()` is a no-op

## Fix

The issue appears to be that `check_code` and `sort_code` have different opinions about whether a trailing newline is required. The fix would involve ensuring both functions use the same normalization logic for trailing newlines. A potential approach:

Either:
1. Make `check_code` return `False` when trailing newline is missing, OR
2. Make `sort_code` preserve the absence of trailing newline when the rest is sorted

The most consistent approach would be option 1, ensuring `check_code` detects the missing trailing newline as a formatting issue that needs correction.