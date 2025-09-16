# Bug Report: LRUDict.get() Fails to Update Access Order for Falsy Values

**Target**: `aws_lambda_powertools.shared.cache_dict.LRUDict.get`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `LRUDict.get()` method fails to update the access order for falsy values (0, False, None, "", [], {}), breaking the LRU (Least Recently Used) eviction semantics.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from aws_lambda_powertools.shared.cache_dict import LRUDict

@given(st.one_of(st.just(0), st.just(False), st.just(""), st.just([]), st.just({}), st.just(None)))
def test_lrudict_get_falsy_values_not_moved_to_end(falsy_value):
    cache = LRUDict(max_items=3)
    cache["a"] = "first"
    cache["b"] = falsy_value
    cache["c"] = "third"
    
    initial_order = list(cache.keys())
    retrieved = cache.get("b")
    order_after_get = list(cache.keys())
    
    assert order_after_get == ['a', 'c', 'b'], f"Falsy value {falsy_value!r} not moved to end"
```

**Failing input**: Any falsy value (0, False, None, "", [], {})

## Reproducing the Bug

```python
from aws_lambda_powertools.shared.cache_dict import LRUDict

cache = LRUDict(max_items=3)
cache["a"] = "first"
cache["b"] = 0
cache["c"] = "third"

print(f"Before get('b'): {list(cache.keys())}")
value = cache.get("b")
print(f"After get('b'): {list(cache.keys())}")
print(f"Expected: ['a', 'c', 'b']")
```

## Why This Is A Bug

The `get()` method uses `if item:` to check whether to move the accessed item to the end of the OrderedDict. This condition evaluates to False for falsy values, causing them not to be marked as recently used. This breaks LRU semantics and can lead to recently accessed items being evicted incorrectly.

## Fix

```diff
--- a/aws_lambda_powertools/shared/cache_dict.py
+++ b/aws_lambda_powertools/shared/cache_dict.py
@@ -26,8 +26,8 @@ class LRUDict(OrderedDict):
 
     def get(self, key, *args, **kwargs):
         item = super().get(key, *args, **kwargs)
-        if item:
-            self.move_to_end(key=key)
+        if key in self:
+            self.move_to_end(key)
         return item
```