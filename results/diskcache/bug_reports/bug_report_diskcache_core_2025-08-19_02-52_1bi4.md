# Bug Report: diskcache.core Text Storage Line Ending Corruption

**Target**: `diskcache.core.Disk`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The Disk class in diskcache.core corrupts text strings containing carriage return characters (`\r`) when storing them to files, converting them to newline characters (`\n`).

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import tempfile
import shutil
from diskcache.core import Disk

@given(
    data=st.one_of(
        st.text(min_size=1000, max_size=2000)
    )
)
@settings(max_examples=50)
def test_disk_large_values(data):
    """Test Disk handles large values by storing to files."""
    tmpdir = tempfile.mkdtemp()
    try:
        # Set min_file_size low to force file storage
        disk = Disk(tmpdir, min_file_size=1000)
        
        size, mode, filename, db_value = disk.store(data, read=False)
        
        # Large values should be stored in files
        assert filename is not None
        assert db_value is None
        assert size > 0
        
        # Should fetch correctly
        retrieved = disk.fetch(mode, filename, db_value, read=False)
        assert retrieved == data  # FAILS when data contains \r
    finally:
        shutil.rmtree(tmpdir)
```

**Failing input**: Any text string over 1000 characters containing `\r` characters

## Reproducing the Bug

```python
import tempfile
import shutil
from diskcache.core import Disk

tmpdir = tempfile.mkdtemp()
try:
    disk = Disk(tmpdir, min_file_size=1000)
    
    # Create a string with carriage return that is large enough to be stored in a file
    original = "0" * 250 + "\r" + "0" * 1000
    
    # Store the value (should go to file due to size)
    size, mode, filename, db_value = disk.store(original, read=False)
    
    # Fetch it back
    retrieved = disk.fetch(mode, filename, db_value, read=False)
    
    # Check if they match
    assert original == retrieved, f"Expected {repr(original[250])}, got {repr(retrieved[250])}"
    
finally:
    shutil.rmtree(tmpdir)
```

## Why This Is A Bug

This violates the fundamental round-trip property that users expect from a cache: storing a value and retrieving it should return the exact same value. The silent conversion of `\r` to `\n` breaks this contract and can cause issues for:

1. Applications that process text with specific line ending requirements
2. Binary data accidentally stored as text
3. Cross-platform applications where line endings matter
4. Data integrity checks that rely on exact string matching

## Fix

The issue occurs because text is written and read using Python's text mode, which applies platform-specific line ending conversions. The fix is to use binary mode with explicit UTF-8 encoding:

```diff
--- a/diskcache/core.py
+++ b/diskcache/core.py
@@ -208,8 +208,9 @@ class Disk:
                 return len(value), MODE_BINARY, filename, None
         elif type_value is str:
             filename, full_path = self.filename(key, value)
-            self._write(full_path, io.StringIO(value), 'x', 'UTF-8')
-            size = op.getsize(full_path)
+            encoded = value.encode('UTF-8')
+            self._write(full_path, io.BytesIO(encoded), 'xb')
+            size = len(encoded)
             return size, MODE_TEXT, filename, None
         elif read:
             reader = ft.partial(value.read, 2**22)
@@ -274,8 +275,8 @@ class Disk:
                     return reader.read()
         elif mode == MODE_TEXT:
             full_path = op.join(self._directory, filename)
-            with open(full_path, 'r', encoding='UTF-8') as reader:
-                return reader.read()
+            with open(full_path, 'rb') as reader:
+                return reader.read().decode('UTF-8')
         elif mode == MODE_PICKLE:
             if value is None:
                 with open(op.join(self._directory, filename), 'rb') as reader:
```