# Bug Report: jurigged.recode.virtual_file Mishandles Special Characters in Name

**Target**: `jurigged.recode.virtual_file`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `virtual_file` function doesn't properly escape angle brackets (`<`, `>`) and newlines in the name parameter, resulting in malformed virtual filenames that violate the expected `<name#number>` format.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import jurigged.recode as recode
import re

@given(st.text())
def test_virtual_file_format_consistency(name):
    """virtual_file should always produce filenames in <name#number> format"""
    filename = recode.virtual_file(name, "content")
    
    # Should always have exactly one < and one >
    assert filename.count("<") == 1
    assert filename.count(">") == 1
    
    # Should match the expected pattern
    match = re.match(r'^<(.*)#\d+>$', filename, re.DOTALL)
    assert match is not None
    
    # Extracted name should match input
    assert match.group(1) == name
```

**Failing input**: `name='<'` or `name='>'` or `name='\n'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')
from jurigged.recode import virtual_file

# Bug 1: Angle brackets break format
name = "<"
filename = virtual_file(name, "test")
print(f"Input: {repr(name)}")
print(f"Output: {repr(filename)}")  # Output: '<<#1>' - has 2 '<' characters!

# Bug 2: Right angle bracket
name = ">"
filename = virtual_file(name, "test")
print(f"Input: {repr(name)}")
print(f"Output: {repr(filename)}")  # Output: '<>#2>' - has 2 '>' characters!

# Bug 3: Newline breaks regex matching
name = "\n"
filename = virtual_file(name, "test")
print(f"Input: {repr(name)}")
print(f"Output: {repr(filename)}")  # Output: '<\n#4>' - contains literal newline
```

## Why This Is A Bug

The virtual_file function creates filenames in the format `<name#number>` for use as virtual file identifiers. When the name contains angle brackets or newlines, the resulting filename violates this format convention:

1. Names with `<` or `>` produce filenames with multiple angle brackets, making it ambiguous where the name ends and the format markers begin
2. Names with newlines create filenames with embedded newlines, which could break line-based parsing or display
3. Code that parses these filenames expecting the `<name#number>` format will fail or produce incorrect results

## Fix

```diff
--- a/jurigged/recode.py
+++ b/jurigged/recode.py
@@ -16,8 +16,12 @@ class OutOfSyncException(Exception):
 
 
 def virtual_file(name, contents):
-    filename = f"<{name}#{next(_count)}>"
+    # Escape special characters that would break the <name#number> format
+    escaped_name = name.replace('\\', '\\\\')  # Escape backslashes first
+    escaped_name = escaped_name.replace('<', '\\<')
+    escaped_name = escaped_name.replace('>', '\\>')
+    escaped_name = escaped_name.replace('\n', '\\n')
+    filename = f"<{escaped_name}#{next(_count)}>"
     linecache.cache[filename] = (None, None, splitlines(contents), filename)
     return filename
```