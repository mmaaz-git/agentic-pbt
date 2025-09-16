# Bug Report: pdfkit.source TypeError with Non-String/Non-FileObj Input

**Target**: `pdfkit.source.Source`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The Source class crashes with a TypeError when initialized with type='file' and a non-string, non-file-like object, instead of raising a meaningful validation error.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pdfkit.source import Source

@given(
    has_read_method=st.booleans(),
    other_attrs=st.lists(st.text(min_size=1, max_size=10), max_size=5)
)
def test_file_object_detection(has_read_method, other_attrs):
    class TestObj:
        pass
    
    obj = TestObj()
    
    for attr in other_attrs:
        setattr(obj, attr, lambda: None)
    
    if has_read_method:
        obj.read = lambda: b"test"
    
    s = Source(obj, 'file')
    assert s.isFileObj() == has_read_method
```

**Failing input**: `has_read_method=False, other_attrs=[]`

## Reproducing the Bug

```python
from pdfkit.source import Source

class CustomObject:
    pass

obj = CustomObject()
s = Source(obj, 'file')
```

## Why This Is A Bug

The Source class should validate input types and provide meaningful error messages. Instead, it passes arbitrary objects to `os.path.exists()` which raises a TypeError. This violates the principle of fail-fast with clear error messages. Users passing incorrect types get a confusing "stat: path should be string, bytes, os.PathLike or integer" error instead of being told their input type is invalid for file sources.

## Fix

```diff
--- a/pdfkit/source.py
+++ b/pdfkit/source.py
@@ -33,11 +33,19 @@ class Source(object):
     def checkFiles(self):
         if isinstance(self.source, list):
             for path in self.source:
+                if not isinstance(path, (basestring, bytes)):
+                    raise TypeError('File source items must be strings or bytes, got %s' % type(path).__name__)
                 if not os.path.exists(path):
                     raise IOError('No such file: %s' % path)
         else:
-            if not hasattr(self.source, 'read') and not os.path.exists(self.source):
-                raise IOError('No such file: %s' % self.source)
+            if not hasattr(self.source, 'read'):
+                if not isinstance(self.source, (basestring, bytes)):
+                    raise TypeError('File source must be a string, bytes, or file-like object with read() method, got %s' % type(self.source).__name__)
+                if not os.path.exists(self.source):
+                    if self.source == '':
+                        raise IOError('Invalid file path: empty string provided')
+                    else:
+                        raise IOError('No such file: %s' % self.source)
 
     def isString(self):
         return 'string' in self.type
```