# Bug Report: rest_framework_api_key.crypto Round-Trip Failure with Dots

**Target**: `rest_framework_api_key.crypto.concatenate` and `rest_framework_api_key.crypto.split`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `concatenate` and `split` functions in `rest_framework_api_key.crypto` fail to round-trip correctly when the left part contains a dot character, violating the invariant that `split(concatenate(left, right))` should equal `(left, right)`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from rest_framework_api_key.crypto import concatenate, split

@given(
    left=st.text(min_size=1, max_size=100),
    right=st.text(min_size=1, max_size=100)
)
def test_concatenate_split_round_trip(left, right):
    """split(concatenate(left, right)) should return (left, right)"""
    concatenated = concatenate(left, right)
    result_left, result_right = split(concatenated)
    assert result_left == left
    assert result_right == right
```

**Failing input**: `left=".", right="0"`

## Reproducing the Bug

```python
from rest_framework_api_key.crypto import concatenate, split

left = "abc.def"
right = "xyz"

concatenated = concatenate(left, right)
result_left, result_right = split(concatenated)

assert result_left == left  # Fails: result_left is "abc" instead of "abc.def"
assert result_right == right  # Fails: result_right is "def.xyz" instead of "xyz"
```

## Why This Is A Bug

The `concatenate` function joins two strings with a dot separator, and `split` is meant to reverse this operation. However, `split` uses Python's `partition('.')` method which splits on the **first** occurrence of a dot. This breaks the round-trip property when the left part contains dots.

This violates the expected contract that these functions form an invertible pair. The API key generation system uses dots as separators between prefix and secret key components. If prefixes can contain dots (which the current implementation allows), this could lead to incorrect parsing of API keys.

## Fix

```diff
--- a/rest_framework_api_key/crypto.py
+++ b/rest_framework_api_key/crypto.py
@@ -15,7 +15,7 @@ def concatenate(left: str, right: str) -> str:
 
 def split(concatenated: str) -> typing.Tuple[str, str]:
-    left, _, right = concatenated.partition(".")
+    left, _, right = concatenated.rpartition(".")
     return left, right
```

The fix changes `partition` to `rpartition`, which splits on the **last** occurrence of a dot. This ensures correct round-tripping when the left part contains dots. However, this would break if the right part is empty and the left part ends with a dot. A more robust solution might use a different separator or encoding scheme.