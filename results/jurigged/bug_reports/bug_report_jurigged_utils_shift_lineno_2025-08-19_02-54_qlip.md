# Bug Report: jurigged.utils.shift_lineno Crashes on Boundary Values

**Target**: `jurigged.utils.shift_lineno`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `shift_lineno` function crashes with ValueError when shifting would result in negative line numbers and with OverflowError when the result exceeds integer limits.

## Property-Based Test

```python
@given(
    original_lineno=st.integers(min_value=1, max_value=100000),
    delta=st.integers()
)
@example(original_lineno=1, delta=-10)  # Test negative result
@example(original_lineno=2**31-100, delta=200)  # Test overflow
def test_shift_lineno_boundary_values(original_lineno, delta):
    """Test shift_lineno with boundary values."""
    def test_func():
        pass
    
    original_code = test_func.__code__
    modified_code = original_code.replace(co_firstlineno=original_lineno)
    
    shifted_code = utils.shift_lineno(modified_code, delta)
    
    expected_lineno = original_lineno + delta
    assert isinstance(shifted_code, types.CodeType)
    assert shifted_code.co_firstlineno == expected_lineno
```

**Failing input**: `original_lineno=1, delta=-10` and `original_lineno=2147483548, delta=200`

## Reproducing the Bug

```python
from jurigged.utils import shift_lineno

def test_func():
    pass

original_code = test_func.__code__

# Bug 1: Negative line number
shifted_code = shift_lineno(original_code.replace(co_firstlineno=1), -10)
# ValueError: co_firstlineno must be a positive integer

# Bug 2: Integer overflow  
shifted_code = shift_lineno(original_code.replace(co_firstlineno=2**31-100), 200)
# OverflowError: Python int too large to convert to C int
```

## Why This Is A Bug

The function doesn't validate that the resulting line number after shifting will be within valid bounds (positive integer within C int limits). This causes crashes instead of gracefully handling edge cases.

## Fix

```diff
def shift_lineno(co, delta):
    if isinstance(co, types.CodeType):
+       new_lineno = co.co_firstlineno + delta
+       # Ensure line number stays within valid bounds
+       if new_lineno < 1:
+           new_lineno = 1
+       elif new_lineno > 2**31 - 1:
+           new_lineno = 2**31 - 1
        return co.replace(
-           co_firstlineno=co.co_firstlineno + delta,
+           co_firstlineno=new_lineno,
            co_consts=tuple(shift_lineno(ct, delta) for ct in co.co_consts),
        )
    else:
        return co
```