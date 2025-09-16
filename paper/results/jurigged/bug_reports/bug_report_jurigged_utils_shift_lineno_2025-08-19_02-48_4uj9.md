# Bug Report: jurigged.utils.shift_lineno ValueError on Negative Line Numbers

**Target**: `jurigged.utils.shift_lineno`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `shift_lineno` function in jurigged.utils crashes with a ValueError when shifting code object line numbers would result in a negative or zero line number.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from jurigged.utils import shift_lineno

def create_simple_code():
    code_str = """
def test():
    pass
"""
    return compile(code_str, "test.py", "exec")

@given(delta=st.integers(min_value=-100, max_value=100))
def test_shift_lineno_round_trip(delta):
    """Shifting by delta then -delta should give original line numbers"""
    original = create_simple_code()
    
    # Shift forward
    shifted = shift_lineno(original, delta)
    
    # Shift back
    restored = shift_lineno(shifted, -delta)
    
    # Line numbers should be restored
    assert restored.co_firstlineno == original.co_firstlineno
```

**Failing input**: `delta=-2`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from jurigged.utils import shift_lineno

code_str = """
def test():
    pass
"""
code_obj = compile(code_str, "test.py", "exec")

shifted = shift_lineno(code_obj, -2)
```

## Why This Is A Bug

The function violates the round-trip property that shifting by delta then -delta should restore the original. It also doesn't gracefully handle cases where the resulting line number would be invalid (< 1). This could occur in legitimate use cases where code is being transformed or when attempting to undo line number shifts.

## Fix

```diff
def shift_lineno(co, delta):
    if isinstance(co, types.CodeType):
+       new_lineno = co.co_firstlineno + delta
+       if new_lineno < 1:
+           new_lineno = 1
        return co.replace(
-           co_firstlineno=co.co_firstlineno + delta,
+           co_firstlineno=new_lineno,
            co_consts=tuple(shift_lineno(ct, delta) for ct in co.co_consts),
        )
    else:
        return co
```