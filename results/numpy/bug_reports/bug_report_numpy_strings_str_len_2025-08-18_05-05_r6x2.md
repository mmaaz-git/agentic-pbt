# Bug Report: numpy.strings.str_len Incorrect Length for Strings with Leading Null Characters

**Target**: `numpy.strings.str_len`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `numpy.strings.str_len` function returns incorrect lengths for strings containing leading null characters (`\x00`), treating them as empty strings instead of counting the null character.

## Property-Based Test

```python
import numpy as np
import numpy.strings as ns
from hypothesis import given, strategies as st

@given(st.text(alphabet=st.just('\x00'), min_size=1, max_size=10))
def test_str_len_null_character_bug(s):
    """Test that str_len handles null characters correctly"""
    arr = np.array([s], dtype=f'U{len(s) + 10}')
    numpy_len = ns.str_len(arr)[0]
    expected_len = len(s)
    assert numpy_len == expected_len, f"str_len('{repr(s)}') = {numpy_len}, expected {expected_len}"
```

**Failing input**: `'\x00'`

## Reproducing the Bug

```python
import numpy as np
import numpy.strings as ns

test_cases = [
    '\x00',          # Single null character
    '\x00\x00',      # Multiple null characters
    'abc\x00',       # Null at end
]

for s in test_cases:
    arr = np.array([s], dtype='U10')
    numpy_len = ns.str_len(arr)[0]
    python_len = len(s)
    if numpy_len != python_len:
        print(f"BUG: str_len({repr(s)}) = {numpy_len}, expected {python_len}")
```

## Why This Is A Bug

The `str_len` function should return the actual length of the string as stored in the NumPy array, matching Python's `len()` function. Null characters are valid Unicode characters and should be counted in the string length. The current behavior is inconsistent:

1. Strings with only null characters return length 0 (incorrect)
2. Strings ending with null characters have the null truncated from the count (incorrect)
3. Strings with null characters in the middle or beginning (followed by other chars) count correctly

This violates the expected invariant that `numpy.strings.str_len(array)[i] == len(array[i])` for all valid Unicode strings.

## Fix

The issue appears to be that `str_len` is using C-style string length calculation which stops at the first null character when the null appears at certain positions. The fix would require modifying the underlying implementation to count all characters in the Unicode string buffer, not stopping at null characters.

```diff
# Conceptual fix in the str_len implementation:
- Use C strlen() or similar null-terminating logic
+ Count all characters in the Unicode buffer up to the dtype's specified size
```

The exact fix would need to be applied in NumPy's C/Cython implementation of the `str_len` ufunc to properly handle embedded null characters in Unicode strings.