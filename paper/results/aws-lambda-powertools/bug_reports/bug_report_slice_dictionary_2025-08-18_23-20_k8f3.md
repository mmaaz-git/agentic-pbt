# Bug Report: slice_dictionary Incorrectly Yields Duplicate Chunks

**Target**: `aws_lambda_powertools.shared.functions.slice_dictionary`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `slice_dictionary` function incorrectly yields duplicate chunks containing the same keys when slicing a dictionary, instead of properly dividing the dictionary into non-overlapping chunks.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from aws_lambda_powertools.shared.functions import slice_dictionary

@given(
    data=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.integers(),
        min_size=0,
        max_size=50
    ),
    chunk_size=st.integers(min_value=1, max_value=20)
)
def test_slice_dictionary_concatenation(data, chunk_size):
    """Test that concatenating sliced dictionary chunks recreates the original"""
    if not data:
        chunks = list(slice_dictionary(data, chunk_size))
        assert chunks == [], "Empty dict should produce no chunks"
        return
    
    chunks = list(slice_dictionary(data, chunk_size))
    
    # Concatenating all chunks should give us back the original dictionary
    reconstructed = {}
    for chunk in chunks:
        reconstructed.update(chunk)
    
    assert reconstructed == data, f"Reconstructed dict doesn't match original"
```

**Failing input**: `data={'0': 0, '00': 0}, chunk_size=1`

## Reproducing the Bug

```python
from aws_lambda_powertools.shared.functions import slice_dictionary

data = {'0': 0, '00': 0}
chunk_size = 1

chunks = list(slice_dictionary(data, chunk_size))
print(f"Chunks: {chunks}")

reconstructed = {}
for chunk in chunks:
    reconstructed.update(chunk)

print(f"Original:      {data}")
print(f"Reconstructed: {reconstructed}")
print(f"Missing keys:  {set(data.keys()) - set(reconstructed.keys())}")
```

## Why This Is A Bug

The function is intended to slice a dictionary into chunks of a specified size. With a dictionary of 2 items and chunk_size=1, it should yield two chunks: one with the first key-value pair and one with the second. However, it yields the same first key twice, causing data loss when reconstructing the dictionary.

The bug is in the implementation: `itertools.islice(data, chunk_size)` always starts from the beginning of the dictionary keys on each iteration, rather than advancing to the next unprocessed keys.

## Fix

```diff
def slice_dictionary(data: dict, chunk_size: int) -> Generator[dict, None, None]:
-    for _ in range(0, len(data), chunk_size):
-        yield {dict_key: data[dict_key] for dict_key in itertools.islice(data, chunk_size)}
+    keys = list(data.keys())
+    for i in range(0, len(keys), chunk_size):
+        yield {key: data[key] for key in keys[i:i+chunk_size]}
```