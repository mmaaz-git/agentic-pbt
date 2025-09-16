# Bug Report: fire.core Flag Detection Functions Return None Instead of Boolean

**Target**: `fire.core._IsFlag`, `fire.core._IsSingleCharFlag`, `fire.core._IsMultiCharFlag`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The flag detection functions in fire.core return None instead of False for many inputs, violating the expected boolean return type indicated by their docstrings and names.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import fire.core as core

@given(st.text(min_size=0, max_size=20))
def test_flag_functions_return_boolean(arg):
    """Test that flag detection functions return boolean values, not None."""
    result = core._IsFlag(arg)
    assert result is True or result is False, \
        f"_IsFlag('{arg}') returned {result} (type: {type(result)}), expected bool"
```

**Failing input**: `'0'`

## Reproducing the Bug

```python
import fire.core as core

result = core._IsFlag('0')
print(f"_IsFlag('0') returns: {repr(result)}")
assert isinstance(result, bool), f"Expected bool, got {type(result)}"
```

## Why This Is A Bug

The functions `_IsSingleCharFlag`, `_IsMultiCharFlag`, and `_IsFlag` are predicate functions that should return boolean values. Their names and docstrings indicate they answer yes/no questions about whether an argument is a flag. Returning None violates this contract and can cause unexpected behavior when the result is used in boolean contexts or type-checked code.

The bug occurs because the functions use `or` operations with regex match results. When `re.match()` returns None and is combined with False using `or`, the expression evaluates to None rather than False.

## Fix

```diff
--- a/fire/core.py
+++ b/fire/core.py
@@ -948,11 +948,11 @@ def _IsFlag(argument):
 
 def _IsSingleCharFlag(argument):
   """Determines if the argument is a single char flag (e.g. '-a')."""
-  return re.match('^-[a-zA-Z]$', argument) or re.match('^-[a-zA-Z]=', argument)
+  return bool(re.match('^-[a-zA-Z]$', argument) or re.match('^-[a-zA-Z]=', argument))
 
 
 def _IsMultiCharFlag(argument):
   """Determines if the argument is a multi char flag (e.g. '--alpha')."""
-  return argument.startswith('--') or re.match('^-[a-zA-Z]', argument)
+  return bool(argument.startswith('--') or re.match('^-[a-zA-Z]', argument))
```