# Bug Report: limits.limits safe_string crashes on non-UTF-8 bytes

**Target**: `limits.limits.safe_string`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `safe_string` function crashes with `UnicodeDecodeError` when given bytes that are not valid UTF-8, despite its docstring claiming to "normalize a byte/str/int or float to a str".

## Property-Based Test

```python
from hypothesis import given, strategies as st, example
from limits.limits import safe_string

@given(st.binary(min_size=1, max_size=10))
@example(b'\xff\xfe')  # Invalid UTF-8 sequence
def test_safe_string_handles_all_bytes(byte_value):
    """safe_string should handle ANY bytes input without crashing"""
    result = safe_string(byte_value)
    assert isinstance(result, str)
```

**Failing input**: `b'\xff\xfe'`

## Reproducing the Bug

```python
from limits.limits import safe_string

invalid_utf8 = b'\xff\xfe'
result = safe_string(invalid_utf8)
```

## Why This Is A Bug

The function accepts `bytes` as a valid input type according to its type hints and docstring, but it calls `value.decode()` without error handling. This causes a crash when the bytes are not valid UTF-8. The function should either:
1. Handle decoding errors gracefully (e.g., with `errors='replace'` or `errors='ignore'`)
2. Document that it only accepts UTF-8 encoded bytes
3. Return a string representation of the bytes when decoding fails

Since the function is used to generate keys for rate limiting, crashing on non-UTF-8 input could cause availability issues if user input contains non-UTF-8 bytes.

## Fix

```diff
def safe_string(value: bytes | str | int | float) -> str:
    """
    normalize a byte/str/int or float to a str
    """
    
    if isinstance(value, bytes):
-       return value.decode()
+       return value.decode('utf-8', errors='replace')
    
    return str(value)
```