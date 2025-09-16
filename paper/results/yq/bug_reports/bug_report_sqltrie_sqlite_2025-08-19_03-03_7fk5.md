# Bug Report: SQLiteTrie Empty String Path Construction Failure

**Target**: `sqltrie.sqlite.SQLiteTrie`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

SQLiteTrie fails to correctly handle keys containing consecutive empty strings due to improper path construction in SQL queries, resulting in KeyError when retrieving values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from sqltrie import SQLiteTrie
import tempfile, os

@given(st.lists(st.text(min_size=0, max_size=5), min_size=1, max_size=3).map(tuple))
def test_empty_string_keys(key):
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    try:
        trie = SQLiteTrie.open(db_path)
        trie[key] = b'value'
        assert trie[key] == b'value'  # Fails for keys with consecutive empty strings
        trie.close()
    finally:
        os.unlink(db_path)
```

**Failing input**: `key=('', '')`

## Reproducing the Bug

```python
import tempfile
import os
from sqltrie import SQLiteTrie

with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
    db_path = f.name

try:
    trie = SQLiteTrie.open(db_path)
    
    key = ('', '')
    value = b'test_value'
    
    trie[key] = value
    result = trie[key]  # Raises KeyError: ('', '')
    
    trie.close()
finally:
    os.unlink(db_path)
```

## Why This Is A Bug

The SQLiteTrie should support any tuple of strings as keys, including empty strings. The issue occurs in the `_traverse()` method which constructs SQL paths using `'/'.join(key)`. When the key contains consecutive empty strings, this produces an invalid path representation that causes the SQL query to fail to find the node.

## Fix

The bug is in the path construction logic in `sqltrie/sqlite/sqlite.py`:

```diff
--- a/sqltrie/sqlite/sqlite.py
+++ b/sqltrie/sqlite/sqlite.py
@@ -187,8 +187,13 @@ class SQLiteTrie(AbstractTrie):
         return pid
 
     def _traverse(self, key):
-        path = "/".join(key).replace("'", "''")
-        self._conn.executescript(STEPS_SQL.format(path=path, root=self._root_id))
+        if not key:
+            path = ""
+        else:
+            # Handle empty strings by using a special separator that won't conflict
+            # Or use a more robust path encoding mechanism
+            path = "/".join(s if s else "\x01" for s in key).replace("'", "''")
+        self._conn.executescript(STEPS_SQL.format(path=path, root=self._root_id))
 
         return self._conn.execute(f"SELECT * FROM {STEPS_TABLE}").fetchall()  # nosec
```