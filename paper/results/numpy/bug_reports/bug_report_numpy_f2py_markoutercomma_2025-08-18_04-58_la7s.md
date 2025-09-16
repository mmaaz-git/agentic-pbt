# Bug Report: numpy.f2py.crackfortran.markoutercomma Crashes on Unbalanced Parentheses

**Target**: `numpy.f2py.crackfortran.markoutercomma`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `markoutercomma` function in numpy's f2py module crashes with an AssertionError when processing strings with unbalanced parentheses, causing f2py to fail when parsing malformed Fortran code.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import numpy.f2py.crackfortran as cf

@given(st.text())
def test_markoutercomma_handles_any_input(text):
    """markoutercomma should handle any string input gracefully."""
    try:
        result = cf.markoutercomma(text)
        assert isinstance(result, str)
    except AssertionError:
        assert False, f"markoutercomma crashes on {text!r}"
```

**Failing input**: `')'`

## Reproducing the Bug

```python
import numpy.f2py.crackfortran as cf

cf.markoutercomma(')')
```

This can also be triggered when f2py parses malformed Fortran code:

```python
import numpy.f2py.crackfortran as cf

with open('test.f90', 'w') as f:
    f.write('''subroutine test()
    real, dimension(10)) :: array
end subroutine''')

cf.crackfortran(['test.f90'])
```

## Why This Is A Bug

The function uses an assertion to check parenthesis balance at the end, which causes a crash instead of handling the error gracefully. This makes f2py fragile when processing malformed Fortran code that might have typos or syntax errors. A parser should provide meaningful error messages rather than crashing with internal assertions.

## Fix

```diff
--- a/numpy/f2py/crackfortran.py
+++ b/numpy/f2py/crackfortran.py
@@ -886,7 +886,10 @@ def markoutercomma(line, comma=','):
                 f -= 1
         before, after = split_by_unquoted(after[1:], comma + '()')
         l += before
-    assert not f, repr((f, line, l))
+    if f != 0:
+        raise ValueError(f"Unbalanced parentheses in input: {line!r} "
+                        f"(balance={f:+d})")
     return l
```