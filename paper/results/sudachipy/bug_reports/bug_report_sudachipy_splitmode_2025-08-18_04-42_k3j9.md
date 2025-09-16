# Bug Report: sudachipy.SplitMode Undocumented Error Behavior

**Target**: `sudachipy.SplitMode`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `SplitMode.__init__` method raises `SudachiError` for invalid mode strings, but this error behavior is not documented in the type hints or docstring.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import sudachipy
from sudachipy import SplitMode

@given(st.text().filter(lambda x: x.upper() not in ["A", "B", "C", ""]))
def test_splitmode_invalid_strings(text):
    """Test that invalid strings behavior matches documentation"""
    # Documentation doesn't mention error behavior for invalid strings
    mode = SplitMode(text)  # Raises undocumented SudachiError
```

**Failing input**: `'0'` (or any string not in ["A", "a", "B", "b", "C", "c"])

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')
from sudachipy import SplitMode

mode = SplitMode("0")
```

## Why This Is A Bug

The type hints in `sudachipy.pyi` define `SplitMode.__init__` as:

```python
def __init__(cls, mode: Optional[SplitModeStr] = "C") -> None:
    """
    Creates a split mode from a string value.
    
    :param mode: string representation of the split mode. One of [A,B,C] in captital or lower case.
        If None, returns SplitMode.C.
    """
```

The documentation specifies valid inputs ("One of [A,B,C]") and the None case behavior, but doesn't mention that invalid strings raise `SudachiError`. This violates the API contract as users cannot know from the documentation that they need to handle this exception.

## Fix

Update the documentation to reflect the actual behavior:

```diff
 def __init__(cls, mode: Optional[SplitModeStr] = "C") -> None:
     """
     Creates a split mode from a string value.
     
     :param mode: string representation of the split mode. One of [A,B,C] in captital or lower case.
         If None, returns SplitMode.C.
+    :raises SudachiError: If mode is not one of [A, B, C] (case insensitive), None, or empty string.
     """
```