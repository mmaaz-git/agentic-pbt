# Bug Report: rest_framework_api_key.crypto Round-Trip Property Violation

**Target**: `rest_framework_api_key.crypto.concatenate` and `rest_framework_api_key.crypto.split`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `split` function fails to correctly inverse the `concatenate` function when the left part contains dots, violating the fundamental round-trip property that `split(concatenate(left, right))` should equal `(left, right)`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from rest_framework_api_key.crypto import concatenate, split

@given(
    left=st.text(min_size=1),
    right=st.text(min_size=1)
)
def test_concatenate_split_round_trip_property(left, right):
    concatenated = concatenate(left, right)
    result_left, result_right = split(concatenated)
    
    assert result_left == left
    assert result_right == right
```

**Failing input**: `left='.'`, `right='0'`

## Reproducing the Bug

```python
from rest_framework_api_key.crypto import concatenate, split

left = "."
right = "0"

concatenated = concatenate(left, right)
result_left, result_right = split(concatenated)

print(f"Input:  ({repr(left)}, {repr(right)})")
print(f"Output: ({repr(result_left)}, {repr(result_right)})")

assert (result_left, result_right) == (left, right), "Round-trip property violated!"
```

## Why This Is A Bug

The `concatenate` and `split` functions are intended to be inverses of each other for combining and separating API key components. However, because both functions use "." as a delimiter and `split` uses `partition(".")` which only splits on the first occurrence, any dots in the left part cause data corruption:

1. When `left` contains dots, `concatenate` creates a string with multiple dots
2. `split` only splits on the first dot, causing the remaining dots and content to be incorrectly assigned to the right part
3. This breaks the round-trip property and can cause API key validation failures

This is particularly problematic in migration `0004_prefix_hashed_key.py` which uses this same `partition(".")` logic to split existing API key IDs.

## Fix

```diff
--- a/rest_framework_api_key/crypto.py
+++ b/rest_framework_api_key/crypto.py
@@ -10,12 +10,15 @@ from django.utils.crypto import constant_time_compare, get_random_string
 
 
 def concatenate(left: str, right: str) -> str:
+    if "." in left:
+        raise ValueError("Left part cannot contain dots")
     return "{}.{}".format(left, right)
 
 
 def split(concatenated: str) -> typing.Tuple[str, str]:
-    left, _, right = concatenated.partition(".")
-    return left, right
+    parts = concatenated.split(".", 1)
+    if len(parts) == 1:
+        return parts[0], ""
+    return parts[0], parts[1]
 
 
 class Sha512ApiKeyHasher(BasePasswordHasher):
```

Note: The fix requires either validating that the left part doesn't contain dots (as shown above) or using a different delimiter/encoding scheme that properly handles dots in both parts.