# Bug Report: SQLiteTrie Incorrect ShortKeyError After Deletion

**Target**: `sqltrie.sqlite.SQLiteTrie`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

SQLiteTrie incorrectly raises ShortKeyError instead of KeyError when accessing a deleted root node, violating the expected exception semantics.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from sqltrie import SQLiteTrie, ShortKeyError
import tempfile, os

@given(st.binary(max_size=100))
def test_deletion_exception_type(value):
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    try:
        trie = SQLiteTrie.open(db_path)
        
        trie[()] = value
        del trie[()]
        
        # After deletion, should raise KeyError, not ShortKeyError
        try:
            _ = trie[()]
            assert False, "Should have raised an exception"
        except KeyError:
            pass  # Correct behavior
        except ShortKeyError:
            assert False, "Should raise KeyError after deletion, not ShortKeyError"
        
        trie.close()
    finally:
        os.unlink(db_path)
```

**Failing input**: Any value

## Reproducing the Bug

```python
import tempfile
import os
from sqltrie import SQLiteTrie, ShortKeyError

with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
    db_path = f.name

try:
    trie = SQLiteTrie.open(db_path)
    
    trie[()] = b'root_value'
    del trie[()]
    
    try:
        result = trie[()]
    except ShortKeyError:
        print("Incorrect: Raised ShortKeyError")
    except KeyError:
        print("Correct: Raised KeyError")
    
    trie.close()
finally:
    os.unlink(db_path)
```

## Why This Is A Bug

According to the API contract, ShortKeyError should only be raised when a key exists as an internal node but has no associated value. After deletion with `del trie[key]`, the node still exists but is marked as having no value. However, semantically, a deleted key should raise KeyError to match Python's dict behavior and user expectations.

## Fix

The issue is in the `__getitem__` method in `sqltrie/sqlite/sqlite.py`:

```diff
--- a/sqltrie/sqlite/sqlite.py
+++ b/sqltrie/sqlite/sqlite.py
@@ -265,9 +265,14 @@ class SQLiteTrie(AbstractTrie):
     def __getitem__(self, key):
         row = self._get_node(key)
         has_value = row["has_value"]
         if not has_value:
-            raise ShortKeyError(key)
+            # Check if this was explicitly deleted vs never had a value
+            # For root node or explicitly deleted nodes, raise KeyError
+            if key == () or self._was_deleted(key):
+                raise KeyError(key)
+            else:
+                raise ShortKeyError(key)
         return row["value"]
```