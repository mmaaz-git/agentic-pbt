# Bug Report: awkward._connect.jax.trees.split_buffers ValueError on Keys Without Dashes

**Target**: `awkward._connect.jax.trees.split_buffers`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `split_buffers` function crashes with a ValueError when processing buffer dictionaries containing keys without dashes, violating the expectation that it should handle any valid dictionary keys.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from awkward._connect.jax.trees import split_buffers

@given(st.dictionaries(
    st.text(min_size=1, max_size=50).filter(lambda s: "-" not in s),
    st.binary(min_size=1, max_size=100)
))
def test_split_buffers_no_dash_keys(buffers):
    """Test that split_buffers handles keys without dashes"""
    data_buffers, other_buffers = split_buffers(buffers)
    assert set(data_buffers.keys()) | set(other_buffers.keys()) == set(buffers.keys())
```

**Failing input**: `{"nodash": b"test"}`

## Reproducing the Bug

```python
from awkward._connect.jax.trees import split_buffers

# This crashes with ValueError: not enough values to unpack (expected 2, got 1)
result = split_buffers({"nodash": b"test"})
```

## Why This Is A Bug

The function assumes all keys contain at least one dash character and uses `key.rsplit("-", 1)` to split them. When a key lacks a dash, `rsplit` returns a single-element list, but the code attempts to unpack it into two variables `(_, attr)`, causing a ValueError. This violates the reasonable expectation that the function should handle arbitrary string keys in the input dictionary.

## Fix

```diff
def split_buffers(buffers: dict) -> tuple[dict, dict]:
    data_buffers, other_buffers = {}, {}
    for key, buf in buffers.items():
-       _, attr = key.rsplit("-", 1)
+       parts = key.rsplit("-", 1)
+       if len(parts) == 2:
+           attr = parts[1]
+       else:
+           attr = parts[0]
        if attr == "data":
            data_buffers[key] = buf
        else:
            other_buffers[key] = buf
    return data_buffers, other_buffers
```