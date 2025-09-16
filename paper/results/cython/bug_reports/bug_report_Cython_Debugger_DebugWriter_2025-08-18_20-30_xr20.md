# Bug Report: CythonDebugWriter Invalid XML Names Crash

**Target**: `Cython.Debugger.DebugWriter.CythonDebugWriter`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

CythonDebugWriter crashes when attempting to create XML elements or attributes with invalid names (e.g., names starting with digits or containing control characters), instead of validating or sanitizing them.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import tempfile
import Cython.Debugger.DebugWriter as DebugWriter

@given(
    st.lists(
        st.tuples(
            st.text(alphabet=st.characters(blacklist_categories=["Cs"], min_codepoint=1), min_size=1, max_size=20).filter(
                lambda x: x.isidentifier() and not x.startswith('.') 
            ),
            st.dictionaries(
                st.text(alphabet=st.characters(blacklist_categories=["Cs"], min_codepoint=1), min_size=1, max_size=10),
                st.text(alphabet=st.characters(blacklist_categories=["Cs"], min_codepoint=1), min_size=0, max_size=50),
                max_size=3
            )
        ),
        min_size=0,
        max_size=10
    )
)
def test_cython_debug_writer_xml_generation(entries):
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = DebugWriter.CythonDebugWriter(tmpdir)
        writer.module_name = "test_module"
        writer.start('Module', {'name': 'test'})
        
        for name, attrs in entries:
            str_attrs = {k: str(v) for k, v in attrs.items()}
            writer.add_entry(name, **str_attrs)
        
        writer.serialize()
```

**Failing input**: `entries=[('A', {'0': ''})]` and `entries=[('0', {})]`

## Reproducing the Bug

```python
import tempfile
import Cython.Debugger.DebugWriter as DebugWriter

with tempfile.TemporaryDirectory() as tmpdir:
    writer = DebugWriter.CythonDebugWriter(tmpdir)
    writer.module_name = "test"
    writer.start('Module', {'name': 'test'})
    
    writer.add_entry('TestEntry', **{'0': 'value'})
    writer.serialize()
```

## Why This Is A Bug

The `is_valid_tag` function only checks for generator argument patterns (`.0`, `.1`) but doesn't validate XML naming rules. XML element and attribute names cannot start with digits or contain control characters. When CythonDebugWriter receives such names, it passes them directly to the XML builder causing a crash. The code should either validate inputs against XML rules or handle/sanitize invalid names gracefully.

## Fix

```diff
--- a/Cython/Debugger/DebugWriter.py
+++ b/Cython/Debugger/DebugWriter.py
@@ -14,6 +14,18 @@ def is_valid_tag(name):
     if isinstance(name, EncodedString):
         if name.startswith(".") and name[1:].isdecimal():
             return False
+    # Check XML naming rules
+    if not name:
+        return False
+    # XML names cannot start with digits
+    if name[0].isdigit():
+        return False
+    # Check for control characters and other invalid XML characters
+    for char in name:
+        if ord(char) < 32 and char not in '\t\n\r':
+            return False
+    # Could also check for valid XML name characters more strictly
+    # but this handles the most common issues
     return True
 
 
@@ -56,8 +68,15 @@ class CythonDebugWriter:
 
     def add_entry(self, name, **attrs):
         if is_valid_tag(name):
-            self.tb.start(name, attrs)
-            self.tb.end(name)
+            # Also validate attribute names
+            valid_attrs = {}
+            for key, value in attrs.items():
+                # Apply similar validation to attribute names
+                if key and not key[0].isdigit() and all(ord(c) >= 32 or c in '\t\n\r' for c in key):
+                    valid_attrs[key] = value
+            if valid_attrs or not attrs:
+                self.tb.start(name, valid_attrs)
+                self.tb.end(name)
 
     def serialize(self):
         self.tb.end('Module')
```