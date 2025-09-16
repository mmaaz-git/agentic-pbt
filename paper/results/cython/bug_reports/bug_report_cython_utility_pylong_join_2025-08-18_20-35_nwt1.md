# Bug Report: Cython.Utility.pylong_join Generates Invalid C Code with Empty Parameters

**Target**: `Cython.Utility.pylong_join`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `pylong_join` function generates syntactically invalid C code when provided with empty strings for `digits_ptr` or `join_type` parameters, potentially causing compilation errors in generated Cython code.

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume
from Cython.Utility import pylong_join

@given(
    st.integers(min_value=1, max_value=20),
    st.text(min_size=0, max_size=20),
    st.text(min_size=0, max_size=20)
)
def test_parameter_validation(count, digits_ptr, join_type):
    """Test that generated code is syntactically valid C."""
    assume(not any(c in digits_ptr for c in '[]()'))
    assume(not any(c in join_type for c in '[]()'))
    
    result = pylong_join(count, digits_ptr, join_type)
    
    # Check for invalid patterns
    if digits_ptr == '':
        # Bare array indexing like [0] is invalid C
        assert not ')[' in result, "Invalid C: bare array indexing without array name"
    
    if join_type == '':
        # Empty cast () is invalid C
        assert not '()' in result, "Invalid C: empty type cast"
```

**Failing input**: `pylong_join(2, '', 'unsigned long')` and `pylong_join(2, 'digits', '')`

## Reproducing the Bug

```python
from Cython.Utility import pylong_join

# Bug 1: Empty digits_ptr generates invalid C code
result1 = pylong_join(2, '', 'unsigned long')
print("With empty digits_ptr:")
print(result1)
# Output: (((((unsigned long)[1]) << PyLong_SHIFT) | (unsigned long)[0]))
# Invalid C: [0] and [1] without array name

# Bug 2: Empty join_type generates invalid C code  
result2 = pylong_join(2, 'digits', '')
print("\nWith empty join_type:")
print(result2)
# Output: ((((()digits[1]) << PyLong_SHIFT) | ()digits[0]))
# Invalid C: empty cast ()

# Both generate syntactically invalid C code that will fail compilation
```

## Why This Is A Bug

The function is a code generator that produces C code snippets. When given empty string parameters, it generates syntactically invalid C code:

1. Empty `digits_ptr` produces bare array indexing `[0]`, `[1]`, etc. without an array name, which is not valid C syntax
2. Empty `join_type` produces empty casts `()` which is not valid C syntax

A code generator should either validate inputs and reject invalid ones, or handle edge cases to always produce valid output. Silently generating invalid code that will cause compilation errors violates the expected behavior.

## Fix

```diff
def pylong_join(count, digits_ptr='digits', join_type='unsigned long'):
    """
    Generate an unrolled shift-then-or loop over the first 'count' digits.
    Assumes that they fit into 'join_type'.

    (((d[2] << n) | d[1]) << n) | d[0]
    """
+   if not digits_ptr:
+       raise ValueError("digits_ptr cannot be empty")
+   if not join_type:
+       raise ValueError("join_type cannot be empty")
+   
    return ('(' * (count * 2) + ' | '.join(
        "(%s)%s[%d])%s)" % (join_type, digits_ptr, _i, " << PyLong_SHIFT" if _i else '')
        for _i in range(count-1, -1, -1)))
```