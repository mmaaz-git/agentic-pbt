# Bug Report: rpdk.core.jsonutils.utils.item_hash Returns Incorrect Hash for All Lists

**Target**: `rpdk.core.jsonutils.utils.item_hash`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `item_hash` function in rpdk.core always returns the same hash value for any list input due to incorrect use of the `.sort()` method, which returns `None` instead of the sorted list.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import hashlib
from rpdk.core.jsonutils.utils import item_hash

@given(st.lists(st.integers(), min_size=1))
def test_item_hash_not_null_hash(lst):
    """Lists should not all hash to the MD5 of 'null'."""
    hash_result = item_hash(lst)
    null_hash = hashlib.md5(b'null').hexdigest()
    assert hash_result != null_hash, f"List {lst} incorrectly hashes to MD5('null'): {hash_result}"
```

**Failing input**: `[0]`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudformation-cli-java-plugin_env/lib/python3.13/site-packages')

from rpdk.core.jsonutils.utils import item_hash
import hashlib

list1 = [1, 2, 3]
list2 = [4, 5, 6]
list3 = []

hash1 = item_hash(list1)
hash2 = item_hash(list2)
hash3 = item_hash(list3)

null_hash = hashlib.md5(b'null').hexdigest()

print(f"Hash of [1, 2, 3]: {hash1}")
print(f"Hash of [4, 5, 6]: {hash2}")
print(f"Hash of []: {hash3}")
print(f"MD5 of 'null': {null_hash}")
print(f"All equal: {hash1 == hash2 == hash3 == null_hash}")
```

## Why This Is A Bug

The function is supposed to compute unique hashes for different data structures to identify them. However, due to the bug on line 32, all lists (regardless of content) hash to the same value - the MD5 of the string "null". This completely breaks the hashing functionality for any data structure containing lists, making it useless for its intended purpose of uniquely identifying different data structures.

The bug occurs because:
1. Line 32: `item = [item_hash(i) for i in item].sort()`
2. The `.sort()` method sorts the list in-place and returns `None`
3. Therefore `item` becomes `None`
4. `json.dumps(None)` produces the string `"null"`
5. All lists hash to MD5("null") = "37a6259cc0c1dae299a7866489dff0bd"

## Fix

```diff
--- a/rpdk/core/jsonutils/utils.py
+++ b/rpdk/core/jsonutils/utils.py
@@ -29,7 +29,7 @@ def item_hash(
     if isinstance(item, dict):
         item = {k: item_hash(v) for k, v in item.items()}
     if isinstance(item, list):
-        item = [item_hash(i) for i in item].sort()
+        item = sorted([item_hash(i) for i in item])
     encoded = json.dumps(item, sort_keys=True).encode()
     dhash.update(encoded)
     return dhash.hexdigest()
```