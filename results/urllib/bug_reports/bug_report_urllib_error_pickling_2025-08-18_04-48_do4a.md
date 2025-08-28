# Bug Report: urllib.error Exception Classes Cannot Be Pickled

**Target**: `urllib.error.URLError`, `urllib.error.HTTPError`, `urllib.error.ContentTooShortError`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

All three exception classes in urllib.error fail to properly support pickling: URLError loses its filename attribute, HTTPError cannot be unpickled at all, and ContentTooShortError cannot be unpickled.

## Property-Based Test

```python
import pickle
from hypothesis import given, strategies as st
import urllib.error

@given(st.text(), st.text(min_size=1))
def test_urlerror_pickling(reason, filename):
    """Test that URLError preserves filename through pickling"""
    err = urllib.error.URLError(reason, filename)
    pickled = pickle.dumps(err)
    unpickled = pickle.loads(pickled)
    assert unpickled.filename == err.filename

@given(st.text(), st.integers(100, 599), st.text(), st.dictionaries(st.text(), st.text()))
def test_httperror_pickling(url, code, msg, hdrs):
    """Test that HTTPError can be pickled"""
    err = urllib.error.HTTPError(url, code, msg, hdrs, None)
    pickled = pickle.dumps(err)
    unpickled = pickle.loads(pickled)
    assert unpickled.code == err.code

@given(st.text(), st.binary())
def test_content_too_short_pickling(message, content):
    """Test ContentTooShortError pickling"""
    err = urllib.error.ContentTooShortError(message, content)
    pickled = pickle.dumps(err)
    unpickled = pickle.loads(pickled)
    assert unpickled.content == err.content
```

**Failing input**: 
- URLError: `reason='', filename='0'`
- HTTPError: any valid inputs
- ContentTooShortError: `message='', content=b''`

## Reproducing the Bug

```python
import pickle
import urllib.error

# Bug 1: URLError loses filename when pickled
err1 = urllib.error.URLError("Connection failed", "http://example.com")
print(f"Before: filename={err1.filename}")
pickled1 = pickle.dumps(err1)
unpickled1 = pickle.loads(pickled1)
print(f"After: filename={unpickled1.filename}")

# Bug 2: HTTPError cannot be unpickled at all
err2 = urllib.error.HTTPError("http://example.com", 404, "Not Found", {}, None)
pickled2 = pickle.dumps(err2)
unpickled2 = pickle.loads(pickled2)

# Bug 3: ContentTooShortError cannot be unpickled
err3 = urllib.error.ContentTooShortError("Download incomplete", b"partial")
pickled3 = pickle.dumps(err3)
unpickled3 = pickle.loads(pickled3)
```

## Why This Is A Bug

Python exceptions should support pickling for use in multiprocessing, distributed systems, and serialization scenarios. The Python documentation states that exceptions should be pickleable. These urllib.error exceptions fail this requirement, causing:
1. Data loss (URLError's filename)
2. Complete failure in distributed/multiprocessing contexts (HTTPError, ContentTooShortError)
3. Inconsistency with other standard library exceptions

## Fix

```diff
--- a/urllib/error.py
+++ b/urllib/error.py
@@ -29,6 +29,13 @@ class URLError(OSError):
         if filename is not None:
             self.filename = filename
 
+    def __reduce__(self):
+        # Preserve filename attribute through pickling
+        args = (self.reason,)
+        if hasattr(self, 'filename') and self.filename is not None:
+            args = (self.reason, self.filename)
+        return (self.__class__, args)
+
     def __str__(self):
         return '<urlopen error %s>' % self.reason
 
@@ -66,6 +73,10 @@ class HTTPError(URLError, urllib.response.addinfourl):
     def headers(self, headers):
         self.hdrs = headers
 
+    def __reduce__(self):
+        # Make HTTPError pickleable
+        return (self.__class__, (self.url, self.code, self.msg, self.hdrs, self.fp))
+
 
 class ContentTooShortError(URLError):
     """Exception raised when downloaded size does not match content-length."""
@@ -73,3 +84,7 @@ class ContentTooShortError(URLError):
     def __init__(self, message, content):
         URLError.__init__(self, message)
         self.content = content
+
+    def __reduce__(self):
+        # Make ContentTooShortError pickleable
+        return (self.__class__, (self.reason, self.content))
```