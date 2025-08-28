# Bug Report: lml_loader Split/Join Round-Trip Failure

**Target**: `lml_loader.DataLoader.split_by_delimiter` and `join_with_delimiter`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The split/join round-trip property fails for empty lists. When joining an empty list and then splitting the result, the output is `['']` instead of the original empty list `[]`.

## Property-Based Test

```python
@given(
    st.lists(st.text(alphabet=st.characters(blacklist_characters=',', min_codepoint=32), min_size=1)),
    st.text(alphabet=st.characters(blacklist_characters='\n\r\t ', min_codepoint=32), min_size=1, max_size=3)
)
def test_split_join_round_trip(items, delimiter):
    loader = DataLoader()
    assume(all(delimiter not in item for item in items))
    joined = loader.join_with_delimiter(items, delimiter)
    split = loader.split_by_delimiter(joined, delimiter)
    assert split == items
```

**Failing input**: `items=[], delimiter='0'` (or any delimiter)

## Reproducing the Bug

```python
from lml_loader import DataLoader

loader = DataLoader()
items = []
delimiter = ','

joined = loader.join_with_delimiter(items, delimiter)
split = loader.split_by_delimiter(joined, delimiter)

print(f"Original: {items}")
print(f"After round-trip: {split}")
print(f"Bug: {split != items}")
```

## Why This Is A Bug

This violates the expected round-trip property that `split(join(x)) = x`. The issue arises because Python's `str.split()` returns `['']` when splitting an empty string, rather than an empty list. This breaks the mathematical property of inverse operations.

## Fix

```diff
--- a/lml_loader.py
+++ b/lml_loader.py
@@ -41,6 +41,8 @@ class DataLoader:
     def split_by_delimiter(self, text: str, delimiter: str = ',') -> List[str]:
         """Split text by delimiter and strip whitespace."""
         if not delimiter:
             return [text]
+        if not text:
+            return []
         return [part.strip() for part in text.split(delimiter)]
```