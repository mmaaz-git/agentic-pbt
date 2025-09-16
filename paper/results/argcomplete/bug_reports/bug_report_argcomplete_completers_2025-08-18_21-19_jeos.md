# Bug Report: argcomplete.completers.FilesCompleter Crashes with Bytes Input

**Target**: `argcomplete.completers.FilesCompleter`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

FilesCompleter.__init__ crashes with TypeError when passed bytes input, despite explicitly checking for and attempting to handle bytes in the code.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import argcomplete.completers

@given(st.one_of(st.text(), st.binary()))
def test_files_completer_string_to_list_conversion(name):
    completer = argcomplete.completers.FilesCompleter(name)
    assert isinstance(completer.allowednames, list)
    assert len(completer.allowednames) == 1
```

**Failing input**: `b''` (empty bytes)

## Reproducing the Bug

```python
import argcomplete.completers

# This crashes with TypeError
completer = argcomplete.completers.FilesCompleter(b'test.txt')
```

## Why This Is A Bug

The FilesCompleter.__init__ method explicitly checks `isinstance(allowednames, (str, bytes))` to handle both string and bytes input, but then tries to call string methods (`.lstrip("*")`) on bytes objects, causing a TypeError. The code's intent to support bytes is clear from the isinstance check, but the implementation is incorrect.

## Fix

```diff
--- a/argcomplete/completers.py
+++ b/argcomplete/completers.py
@@ -52,7 +52,12 @@ class FilesCompleter(BaseCompleter):
         if isinstance(allowednames, (str, bytes)):
             allowednames = [allowednames]
 
-        self.allowednames = [x.lstrip("*").lstrip(".") for x in allowednames]
+        self.allowednames = []
+        for x in allowednames:
+            if isinstance(x, bytes):
+                x = x.decode('utf-8', errors='replace')
+            self.allowednames.append(x.lstrip("*").lstrip("."))
+
         self.directories = directories
```