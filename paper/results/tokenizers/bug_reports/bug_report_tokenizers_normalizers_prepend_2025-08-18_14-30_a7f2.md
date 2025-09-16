# Bug Report: tokenizers.normalizers.Prepend fails on empty string

**Target**: `tokenizers.normalizers.Prepend`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The Prepend normalizer fails to add the prefix when given an empty string, returning an empty string instead of the expected prefix.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import tokenizers.normalizers as norm

@given(st.text(min_size=1, max_size=10))
def test_prepend_on_empty_string(prefix):
    normalizer = norm.Prepend(prefix)
    result = normalizer.normalize_str("")
    assert result == prefix
```

**Failing input**: Any non-empty prefix with empty string input

## Reproducing the Bug

```python
import tokenizers.normalizers as norm

prepend = norm.Prepend("prefix")
result = prepend.normalize_str("")
print(f"Result: '{result}'")
print(f"Expected: 'prefix'")
assert result == "prefix"  # Fails - result is ""
```

## Why This Is A Bug

The Prepend normalizer is designed to add a prefix to strings. This should work consistently for all strings, including empty strings. The current behavior violates the expected contract that `Prepend(prefix).normalize_str(text)` should always equal `prefix + text`.

## Fix

The underlying implementation needs to be fixed to handle empty strings correctly. The fix would involve ensuring the prepend operation occurs even when the input string is empty.