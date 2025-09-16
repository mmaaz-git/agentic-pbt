# Bug Report: aws_lambda_powertools.shared.functions.slice_dictionary Returns Duplicate Chunks

**Target**: `aws_lambda_powertools.shared.functions.slice_dictionary`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `slice_dictionary` function incorrectly returns the same chunk multiple times instead of properly slicing the dictionary into different parts, causing data loss and duplication.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from aws_lambda_powertools.shared.functions import slice_dictionary

@given(
    data=st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(st.integers(), st.text(), st.booleans()),
        min_size=0,
        max_size=100
    ),
    chunk_size=st.integers(min_value=1, max_value=20)
)
def test_slice_dictionary_confluence(data, chunk_size):
    """Test that sliced dictionary chunks can be reconstructed to the original."""
    chunks = list(slice_dictionary(data, chunk_size))
    
    # Reconstruct the dictionary from chunks
    reconstructed = {}
    for chunk in chunks:
        reconstructed.update(chunk)
    
    assert reconstructed == data, f"Reconstruction failed: {data} != {reconstructed}"
```

**Failing input**: `data={'0': 0, '00': 0}, chunk_size=1`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')
from aws_lambda_powertools.shared.functions import slice_dictionary

# Example 1: Lost keys
data = {'0': 0, '00': 0}
chunks = list(slice_dictionary(data, chunk_size=1))
print(f"Original: {data}")
print(f"Chunks: {chunks}")
# Output: Chunks: [{'0': 0}, {'0': 0}]
# Expected: [{'0': 0}, {'00': 0}]

# Example 2: All chunks are identical
data = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5}
chunks = list(slice_dictionary(data, chunk_size=2))
print(f"Original: {data}")
print(f"Chunks: {chunks}")
# Output: [{'a': 1, 'b': 2}, {'a': 1, 'b': 2}, {'a': 1, 'b': 2}]
# Expected: [{'a': 1, 'b': 2}, {'c': 3, 'd': 4}, {'e': 5}]
```

## Why This Is A Bug

The function is supposed to split a dictionary into chunks of the specified size, but instead it repeatedly yields the same first `chunk_size` items. This violates the expected behavior of:
1. Each key appearing exactly once across all chunks
2. Chunks being different slices of the original dictionary
3. Being able to reconstruct the original dictionary from the chunks

## Fix

```diff
--- a/aws_lambda_powertools/shared/functions.py
+++ b/aws_lambda_powertools/shared/functions.py
@@ -141,5 +141,8 @@ def powertools_debug_is_set() -> bool:
 
 
 def slice_dictionary(data: dict, chunk_size: int) -> Generator[dict, None, None]:
-    for _ in range(0, len(data), chunk_size):
-        yield {dict_key: data[dict_key] for dict_key in itertools.islice(data, chunk_size)}
+    it = iter(data)
+    for _ in range(0, len(data), chunk_size):
+        chunk_keys = list(itertools.islice(it, chunk_size))
+        if chunk_keys:
+            yield {dict_key: data[dict_key] for dict_key in chunk_keys}
```