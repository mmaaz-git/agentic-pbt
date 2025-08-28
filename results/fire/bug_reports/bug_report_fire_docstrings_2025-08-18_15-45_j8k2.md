# Bug Report: fire.docstrings Type Inconsistency in _line_is_hyphens

**Target**: `fire.docstrings._line_is_hyphens`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `_line_is_hyphens` function returns an empty string `''` instead of `False` when given an empty string input, violating its contract to return a boolean.

## Property-Based Test

```python
@given(st.text())
def test_line_is_hyphens_correctness(line):
    """Test that _line_is_hyphens correctly identifies hyphen-only lines."""
    result = docstrings._line_is_hyphens(line)
    
    # According to implementation: line and not line.strip('-')
    # This means: line is not empty AND stripping all hyphens leaves empty string
    expected = bool(line and not line.strip('-'))
    
    assert result == expected
```

**Failing input**: `''`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
from fire import docstrings

line = ''
result = docstrings._line_is_hyphens(line)
print(f"Input: {repr(line)}")
print(f"Result: {repr(result)}")
print(f"Result type: {type(result)}")
print(f"Expected type: {type(False)}")

assert isinstance(result, bool), f"Expected bool, got {type(result)}"
```

## Why This Is A Bug

The function's docstring states "Returns whether the line is entirely hyphens", implying a boolean return value. However, when the input is an empty string, the function returns `''` (a string) instead of `False` (a boolean). This violates the function's contract and creates type inconsistency.

The bug occurs because the expression `line and not line.strip('-')` short-circuits when `line` is empty, returning the empty string rather than a boolean.

## Fix

```diff
def _line_is_hyphens(line):
  """Returns whether the line is entirely hyphens (and not blank)."""
-  return line and not line.strip('-')
+  return bool(line and not line.strip('-'))
```