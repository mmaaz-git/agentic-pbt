# Bug Report: slice_dictionary Loses Keys During Chunking

**Target**: `aws_lambda_powertools.shared.functions.slice_dictionary`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `slice_dictionary` function loses dictionary keys when creating chunks, returning duplicate chunks with incorrect keys instead of properly slicing the dictionary.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from aws_lambda_powertools.shared.functions import slice_dictionary

@given(
    st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), min_size=0, max_size=20),
    st.integers(min_value=1, max_value=10)
)
def test_slice_dictionary_preserves_all_items(data, chunk_size):
    chunks = list(slice_dictionary(data, chunk_size))
    reconstructed = {}
    for chunk in chunks:
        reconstructed.update(chunk)
    assert reconstructed == data
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

print(f"Original: {data}")
print(f"Reconstructed: {reconstructed}")
assert reconstructed == data
```

## Why This Is A Bug

The function incorrectly uses `itertools.islice(data, chunk_size)` which slices the dictionary object itself, not its keys. This causes the same keys to be repeated in multiple chunks, leading to data loss. When the dictionary has keys like '0' and '00', both chunks end up with the same key '0'.

## Fix

```diff
--- a/aws_lambda_powertools/shared/functions.py
+++ b/aws_lambda_powertools/shared/functions.py
@@ -141,8 +141,10 @@ def powertools_debug_is_set() -> bool:
 
 
 def slice_dictionary(data: dict, chunk_size: int) -> Generator[dict, None, None]:
-    for _ in range(0, len(data), chunk_size):
-        yield {dict_key: data[dict_key] for dict_key in itertools.islice(data, chunk_size)}
+    keys = list(data.keys())
+    for i in range(0, len(keys), chunk_size):
+        chunk_keys = keys[i:i + chunk_size]
+        yield {key: data[key] for key in chunk_keys}
 
 
 def extract_event_from_common_models(data: Any) -> dict | Any:
```