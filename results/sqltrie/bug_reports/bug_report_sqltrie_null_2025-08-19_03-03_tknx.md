# Bug Report: SQLiteTrie Null Character Embedded SQL Error

**Target**: `sqltrie.sqlite.SQLiteTrie`
**Severity**: Medium  
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

SQLiteTrie crashes with ValueError when keys contain null characters (\x00) due to SQL string embedding issues in the executescript() method.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from sqltrie import SQLiteTrie
import tempfile, os

@given(st.lists(st.text(alphabet=st.characters(min_codepoint=0, max_codepoint=127)), min_size=1, max_size=3).map(tuple))
def test_null_character_keys(key):
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    try:
        trie = SQLiteTrie.open(db_path)
        trie.view(key)  # Crashes when key contains '\x00'
        trie.close()
    finally:
        os.unlink(db_path)
```

**Failing input**: `key=('\x00',)`

## Reproducing the Bug

```python
import tempfile
import os
from sqltrie import SQLiteTrie

with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
    db_path = f.name

try:
    trie = SQLiteTrie.open(db_path)
    
    key = ('\x00',)
    view = trie.view(key)  # Raises ValueError: embedded null character
    
    trie.close()
finally:
    os.unlink(db_path)
```

## Why This Is A Bug

SQLiteTrie should handle all valid Python strings as key components, including those with null characters. The crash occurs because the `_traverse()` method constructs SQL strings directly with string formatting, and SQLite's executescript() cannot handle embedded null characters in the SQL text.

## Fix

The issue is in the path construction and SQL execution in `sqltrie/sqlite/sqlite.py`:

```diff
--- a/sqltrie/sqlite/sqlite.py
+++ b/sqltrie/sqlite/sqlite.py
@@ -187,8 +187,16 @@ class SQLiteTrie(AbstractTrie):
         return pid
 
     def _traverse(self, key):
-        path = "/".join(key).replace("'", "''")
-        self._conn.executescript(STEPS_SQL.format(path=path, root=self._root_id))
+        # Encode the path to handle special characters including null bytes
+        def encode_segment(s):
+            # URL-encode problematic characters
+            return s.replace('\\', '\\\\').replace('\x00', '\\0').replace("'", "''")
+        
+        if not key:
+            path = ""
+        else:
+            path = "/".join(encode_segment(s) for s in key)
+        self._conn.executescript(STEPS_SQL.format(path=path, root=self._root_id))
 
         return self._conn.execute(f"SELECT * FROM {STEPS_TABLE}").fetchall()  # nosec
```