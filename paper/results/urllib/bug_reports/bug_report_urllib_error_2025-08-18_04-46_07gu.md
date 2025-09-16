# Bug Report: urllib.error Pickling Issues

**Target**: `urllib.error.URLError` and `urllib.error.ContentTooShortError`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

URLError and ContentTooShortError do not properly support pickling, causing loss of the filename attribute in URLError and complete failure to unpickle ContentTooShortError.

## Property-Based Test

```python
import pickle
from hypothesis import given, strategies as st
import urllib.error

@given(st.text(), st.text(min_size=1))
def test_urlerror_pickling(reason, filename):
    """Test that URLError can be pickled and unpickled correctly"""
    err = urllib.error.URLError(reason, filename)
    
    pickled = pickle.dumps(err)
    unpickled = pickle.loads(pickled)
    
    assert unpickled.filename == err.filename

@given(st.text(), st.binary())
def test_content_too_short_pickling(message, content):
    """Test ContentTooShortError pickling"""
    err = urllib.error.ContentTooShortError(message, content)
    
    pickled = pickle.dumps(err)
    unpickled = pickle.loads(pickled)
    
    assert unpickled.content == err.content
```

**Failing input**: For URLError: `reason='', filename='0'`; For ContentTooShortError: `message='', content=b''`

## Reproducing the Bug

```python
import pickle
import urllib.error

# Bug 1: URLError loses filename when pickled
err1 = urllib.error.URLError("Connection failed", "http://example.com")
pickled1 = pickle.dumps(err1)
unpickled1 = pickle.loads(pickled1)
assert unpickled1.filename == err1.filename  # AssertionError: None != 'http://example.com'

# Bug 2: ContentTooShortError cannot be unpickled
err2 = urllib.error.ContentTooShortError("Download incomplete", b"partial")
pickled2 = pickle.dumps(err2)
unpickled2 = pickle.loads(pickled2)  # TypeError: missing 1 required positional argument: 'content'
```

## Why This Is A Bug

Python exceptions should support pickling for distributed systems, multiprocessing, and serialization. The standard library's own exceptions should properly preserve all their attributes through pickle/unpickle cycles. The current implementation breaks this expectation, causing data loss (URLError) or complete failure (ContentTooShortError).

## Fix

```diff
--- a/urllib/error.py
+++ b/urllib/error.py
@@ -29,6 +29,11 @@ class URLError(OSError):
         if filename is not None:
             self.filename = filename
 
+    def __reduce__(self):
+        args = (self.reason,)
+        if hasattr(self, 'filename'):
+            args = (self.reason, self.filename)
+        return (self.__class__, args)
+
     def __str__(self):
         return '<urlopen error %s>' % self.reason
 
@@ -73,3 +78,7 @@ class ContentTooShortError(URLError):
     def __init__(self, message, content):
         URLError.__init__(self, message)
         self.content = content
+
+    def __reduce__(self):
+        return (self.__class__, (self.reason, self.content))
```