# Bug Report: diskcache Cache.incr() and Cache.decr() fail with large integers

**Target**: `diskcache.Cache.incr()` and `diskcache.Cache.decr()`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `Cache.incr()` and `Cache.decr()` methods fail when attempting to increment or decrement integer values that exceed SQLite's 64-bit signed integer range, resulting in either a TypeError or OverflowError.

## Property-Based Test

```python
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize
from hypothesis import strategies as st
import tempfile
from diskcache import Cache

class CacheStateMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.tmpdir = tempfile.mkdtemp()
        self.cache = Cache(self.tmpdir)
        self.model = {}
    
    @rule(
        key=st.text(min_size=1, max_size=20),
        value=st.integers()
    )
    def set_item(self, key, value):
        self.cache.set(key, value)
        self.model[key] = value
    
    @rule(
        key=st.text(min_size=1, max_size=20),
        delta=st.integers(min_value=-100, max_value=100)
    )
    def increment_item(self, key, delta):
        if key in self.model and isinstance(self.model[key], int):
            new_value = self.cache.incr(key, delta)
            self.model[key] += delta
            assert new_value == self.model[key]
```

**Failing input**: `set_item(key='0', value=9_223_372_036_854_775_808)` followed by `increment_item(key='0', delta=1)`

## Reproducing the Bug

```python
import tempfile
from diskcache import Cache

# Bug 1: Large integers stored as pickled bytes cause TypeError
with tempfile.TemporaryDirectory() as tmpdir:
    cache = Cache(tmpdir)
    
    # Set a large integer value (2^63, beyond SQLite's integer range)
    large_int = 9_223_372_036_854_775_808
    cache.set('key', large_int)
    
    # Both incr and decr fail with: TypeError: can't concat int to bytes
    cache.incr('key', 1)  # Fails
    cache.decr('key', 1)  # Also fails

# Bug 2: Incrementing near SQLite's limit causes OverflowError  
with tempfile.TemporaryDirectory() as tmpdir:
    cache = Cache(tmpdir)
    
    # Set value near SQLite's max
    near_max = 9_223_372_036_854_775_700
    cache.set('key', near_max)
    
    # This fails with: OverflowError: Python int too large to convert to SQLite INTEGER
    cache.incr('key', 200)
```

## Why This Is A Bug

The `Cache.incr()` documentation states it "Increment value by delta for item with key" and "Assumes value may be stored in a SQLite column", but it doesn't handle the case where integers exceed SQLite's range and get pickled instead. The method should either:

1. Handle pickled integer values correctly by unpickling them before incrementing
2. Raise a more informative error explaining the limitation
3. Document that incr() only works with integers within SQLite's range

## Fix

The issue occurs in `diskcache/core.py` at line 1080 where `value += delta` is executed without checking if the value needs to be unpickled first. Here's a potential fix:

```diff
--- a/diskcache/core.py
+++ b/diskcache/core.py
@@ -1063,7 +1063,7 @@ class Cache:
                 return value
 
-            ((rowid, expire_time, filename, value),) = rows
+            ((rowid, expire_time, filename, db_value),) = rows
 
             if expire_time is not None and expire_time < now:
                 if default is None:
@@ -1077,7 +1077,22 @@ class Cache:
                 cleanup(filename)
                 return value
 
-            value += delta
+            # Check if value needs to be unpickled
+            if filename is not None:
+                # Value was pickled, need to fetch it properly
+                mode = MODE_PICKLE
+                value = self._disk.fetch(mode, filename, db_value, False)
+                value += delta
+                # Re-store the incremented value
+                size, mode, new_filename, new_db_value = self._disk.store(value, False, key=key)
+                columns = 'store_time = ?, size = ?, mode = ?, filename = ?, value = ?'
+                update = 'UPDATE Cache SET %s WHERE rowid = ?' % columns
+                sql(update, (now, size, mode, new_filename, new_db_value, rowid))
+                cleanup(filename)
+            else:
+                # Regular integer, can increment directly
+                value = db_value
+                value += delta
 
             columns = 'store_time = ?, value = ?'
             update_column = EVICTION_POLICY[self.eviction_policy]['get']
```

Note: A more complete fix would need to handle the MODE_PICKLE case properly and ensure the value is an integer before incrementing.