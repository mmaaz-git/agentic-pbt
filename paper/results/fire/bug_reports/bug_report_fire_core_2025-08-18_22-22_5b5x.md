# Bug Report: fire.core _IsFlag Functions Return Inconsistent Types

**Target**: `fire.core._IsFlag`, `fire.core._IsSingleCharFlag`, `fire.core._IsMultiCharFlag`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `_IsFlag`, `_IsSingleCharFlag`, and `_IsMultiCharFlag` functions in fire.core return inconsistent types (None, Match objects, or bool) instead of consistently returning boolean values as their names and docstrings suggest.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import re
from fire import core

@given(st.text())
def test_is_single_char_flag_pattern(argument):
    """Property: Single char flags should return boolean."""
    result = core._IsSingleCharFlag(argument)
    
    # Check against the regex patterns used
    pattern1 = bool(re.match('^-[a-zA-Z]$', argument))
    pattern2 = bool(re.match('^-[a-zA-Z]=', argument))
    
    assert result == (pattern1 or pattern2)
```

**Failing input**: `''` (empty string)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
from fire import core

# Demonstrate inconsistent return types
test_inputs = ['', 'hello', '-a', '--flag']

for arg in test_inputs:
    result = core._IsFlag(arg)
    print(f"_IsFlag({arg!r}) = {result!r} (type: {type(result).__name__})")

# Output shows:
# _IsFlag('') = None (type: NoneType)
# _IsFlag('hello') = None (type: NoneType)  
# _IsFlag('-a') = <re.Match object...> (type: Match)
# _IsFlag('--flag') = True (type: bool)
```

## Why This Is A Bug

The functions are documented as "Determines if the argument is a flag" which implies a boolean return value. However, they return:
- `None` when no regex matches (instead of `False`)
- `Match` objects when regex matches (instead of `True`)
- `True` only when `startswith('--')` is used

This violates the principle of least surprise and can cause subtle bugs in code that expects consistent boolean returns, such as:
- `_IsFlag(x) == False` fails for None returns
- JSON serialization behaves differently for different return types
- Type checking tools expect boolean returns based on function names

## Fix

```diff
--- a/fire/core.py
+++ b/fire/core.py
@@ -949,12 +949,12 @@ def _IsFlag(argument):
 
 def _IsSingleCharFlag(argument):
   """Determines if the argument is a single char flag (e.g. '-a')."""
-  return re.match('^-[a-zA-Z]$', argument) or re.match('^-[a-zA-Z]=', argument)
+  return bool(re.match('^-[a-zA-Z]$', argument) or re.match('^-[a-zA-Z]=', argument))
 
 
 def _IsMultiCharFlag(argument):
   """Determines if the argument is a multi char flag (e.g. '--alpha')."""
-  return argument.startswith('--') or re.match('^-[a-zA-Z]', argument)
+  return argument.startswith('--') or bool(re.match('^-[a-zA-Z]', argument))
 
 
 def _IsFlag(argument):
```