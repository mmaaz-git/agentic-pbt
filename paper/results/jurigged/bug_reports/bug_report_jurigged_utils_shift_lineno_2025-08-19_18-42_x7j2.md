# Bug Report: jurigged.utils.shift_lineno Invalid Line Number Handling

**Target**: `jurigged.utils.shift_lineno`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `shift_lineno` function in jurigged fails when shifting code object line numbers to non-positive values, either crashing with ValueError or silently allowing invalid line 0.

## Property-Based Test

```python
@given(
    delta=st.integers(min_value=-100, max_value=100),
    initial_lineno=st.integers(min_value=1, max_value=1000)
)
def test_shift_lineno_code_object(delta, initial_lineno):
    """Test that shift_lineno correctly shifts line numbers in code objects"""
    code_str = """
def test_func():
    pass
"""
    
    compiled = compile(code_str, '<test>', 'exec')
    
    for const in compiled.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'test_func':
            func_code = const
            break
    else:
        assume(False)
    
    shifted = shift_lineno(func_code, delta)
    
    assert shifted.co_firstlineno == func_code.co_firstlineno + delta
```

**Failing input**: `delta=-3` (with function at line 2)

## Reproducing the Bug

```python
import types
from jurigged.utils import shift_lineno

code_str = """
def test_func():
    pass
"""

compiled = compile(code_str, '<test>', 'exec')
func_code = next(c for c in compiled.co_consts if isinstance(c, types.CodeType))

print(f"Original line: {func_code.co_firstlineno}")  # Line 2

# Case 1: Shift to negative line number
try:
    shifted = shift_lineno(func_code, -3)  # Would be line -1
except ValueError as e:
    print(f"ValueError: {e}")  # co_firstlineno must be a positive integer

# Case 2: Shift to line 0 (also invalid but doesn't error!)
shifted = shift_lineno(func_code, -2)  # Line 0
print(f"Shifted to line: {shifted.co_firstlineno}")  # Prints 0 - should error!
```

## Why This Is A Bug

Python line numbers must be positive integers (starting from 1). The function fails inconsistently:
- Negative line numbers raise ValueError from Python's code.replace()
- Line 0 is silently accepted but is invalid (may cause issues downstream)
- The function is used in codetools.py:705 where negative deltas can occur when `lineno < co.co_firstlineno`

## Fix

```diff
--- a/jurigged/utils.py
+++ b/jurigged/utils.py
@@ -52,6 +52,9 @@
 def shift_lineno(co, delta):
     if isinstance(co, types.CodeType):
+        new_lineno = co.co_firstlineno + delta
+        if new_lineno < 1:
+            raise ValueError(f"Shifting line number by {delta} would result in invalid line {new_lineno}")
         return co.replace(
             co_firstlineno=co.co_firstlineno + delta,
             co_consts=tuple(shift_lineno(ct, delta) for ct in co.co_consts),
```