# Bug Report: tokenizers.normalizers.Strip doesn't handle all whitespace characters

**Target**: `tokenizers.normalizers.Strip`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The Strip normalizer fails to remove certain whitespace characters that Python's `str.isspace()` recognizes as whitespace, such as the unit separator character (`\x1f`).

## Property-Based Test

```python
from hypothesis import given, strategies as st
import tokenizers.normalizers as norm

@given(st.text())
def test_strip_removes_all_whitespace(text):
    normalizer = norm.Strip()
    result = normalizer.normalize_str(text)
    if result:
        assert not result[0].isspace()
        assert not result[-1].isspace()
```

**Failing input**: `'\x1f'` (unit separator character)

## Reproducing the Bug

```python
import tokenizers.normalizers as norm

strip = norm.Strip()
text = "\x1f"  # Unit separator character (ASCII 31)
result = strip.normalize_str(text)

print(f"Input: {repr(text)}")
print(f"Output: {repr(result)}")
print(f"Output length: {len(result)}")
print(f"Python considers input as whitespace: {text.isspace()}")
print(f"Output still contains whitespace: {result.isspace() if result else False}")

assert result == "" or not result.isspace()  # Fails - result is '\x1f'
```

## Why This Is A Bug

The Strip normalizer is expected to remove whitespace from both ends of a string, similar to Python's `str.strip()`. However, it doesn't recognize all Unicode whitespace characters that Python recognizes. This inconsistency can lead to unexpected behavior where strings that appear to be "whitespace-only" are not fully stripped.

## Fix

The Strip normalizer should be updated to recognize and remove all Unicode whitespace characters, matching the behavior of Python's `str.strip()` method or at least handling all ASCII control characters that are considered whitespace.