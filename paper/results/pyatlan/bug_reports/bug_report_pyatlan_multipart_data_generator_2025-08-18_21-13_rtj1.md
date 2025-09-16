# Bug Report: pyatlan.multipart_data_generator Header Injection Vulnerability

**Target**: `pyatlan.multipart_data_generator.MultipartDataGenerator`
**Severity**: High
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The MultipartDataGenerator class fails to properly escape special characters in filenames, allowing HTTP header injection attacks through CRLF sequences and breaking multipart/form-data structure integrity.

## Property-Based Test

```python
from hypothesis import given, strategies as st, example
from pyatlan.multipart_data_generator import MultipartDataGenerator
import io

@given(st.text(min_size=1, max_size=100))
@example('test.txt\r\nX-Injected: value')
def test_no_header_injection(filename):
    """Filenames should not allow header injection attacks"""
    gen = MultipartDataGenerator()
    mock_file = io.BytesIO(b"content")
    gen.add_file(mock_file, filename)
    result = gen.get_post_data()
    
    content_type_count = result.count(b'Content-Type:')
    assert content_type_count == 1, f"Found {content_type_count} Content-Type headers, expected 1"
```

**Failing input**: `'test.txt\r\nX-Injected: value'`

## Reproducing the Bug

```python
import io
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')
from pyatlan.multipart_data_generator import MultipartDataGenerator

gen = MultipartDataGenerator()
mock_file = io.BytesIO(b"malicious content")

malicious_filename = "test.txt\r\nX-Injected-Header: malicious-value\r\nContent-Type: text/html"
gen.add_file(mock_file, malicious_filename)
result = gen.get_post_data()

print("Injected headers found:", result.count(b'Content-Type:') > 1)
print("Headers in output:")
for line in result.split(b'\r\n'):
    if b'X-Injected' in line or b'Content-Type' in line:
        print(" ", line)
```

## Why This Is A Bug

This violates RFC 7578 (Multipart Form Data) which requires proper escaping of special characters in header parameters. The vulnerability allows:

1. **Header Injection**: Attackers can inject arbitrary HTTP headers by including CRLF sequences in filenames
2. **Content-Type Override**: Multiple Content-Type headers can be injected, potentially bypassing security filters
3. **Parser Confusion**: Malformed multipart structures can cause parsing ambiguities

This is a security vulnerability that could be exploited in web applications using this library for file uploads.

## Fix

```diff
--- a/pyatlan/multipart_data_generator.py
+++ b/pyatlan/multipart_data_generator.py
@@ -30,6 +30,15 @@ class MultipartDataGenerator(object):
         self.chunk_size = chunk_size
 
     def add_file(self, file, filename):
+        # Escape special characters in filename to prevent header injection
+        # According to RFC 2388 and RFC 7578, quotes and backslashes should be escaped
+        # and control characters should be removed or encoded
+        if filename:
+            # Remove control characters (including CR, LF)
+            filename = ''.join(c for c in filename if ord(c) >= 32 and c != '\x7f')
+            # Escape quotes and backslashes
+            filename = filename.replace('\\', '\\\\').replace('"', '\\"')
+        
         # Write the 'name' part (name="image")
         self._write(self.param_header())
         self._write(self.line_break)
```