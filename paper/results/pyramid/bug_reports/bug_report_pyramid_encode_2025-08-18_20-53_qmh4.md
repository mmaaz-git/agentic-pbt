# Bug Report: pyramid.encode UnicodeEncodeError on Surrogate Characters

**Target**: `pyramid.encode.urlencode`, `pyramid.encode.url_quote`, `pyramid.url.parse_url_overrides`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The URL encoding functions in pyramid.encode crash with UnicodeEncodeError when processing Unicode surrogate characters (U+D800-U+DFFF), potentially causing denial of service when handling user input.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyramid.encode import urlencode

@given(
    st.lists(
        st.tuples(
            st.text(min_size=1),
            st.text()
        ),
        min_size=0,
        max_size=5
    )
)
def test_urlencode_handles_all_unicode(query_list):
    """urlencode should handle all valid Python strings without crashing"""
    result = urlencode(query_list)
    assert isinstance(result, str)
```

**Failing input**: `[('\ud800', 'value')]`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')
from pyramid.encode import urlencode, url_quote

# Test 1: urlencode crashes
result = urlencode({chr(0xD800): 'value'})

# Test 2: url_quote crashes  
result = url_quote(chr(0xD800))

# Test 3: parse_url_overrides crashes
from pyramid.url import parse_url_overrides

class MockRequest:
    application_url = "http://example.com"

request = MockRequest()
kw = {'_query': {chr(0xD800): 'test'}}
app_url, qs, anchor = parse_url_overrides(request, kw)
```

## Why This Is A Bug

Unicode surrogate characters (U+D800-U+DFFF) are valid in Python strings even though they cannot be encoded to UTF-8. These characters can appear in user input through:
- Malformed JSON/XML parsing
- Broken character encoding/decoding
- Malicious user input attempting DoS

The functions should either:
1. Handle surrogates gracefully (skip/replace them)
2. Document this limitation clearly
3. Provide better error messages

Currently, any web application using Pyramid that processes user-controlled query parameters could crash when encountering surrogate characters.

## Fix

```diff
--- a/pyramid/encode.py
+++ b/pyramid/encode.py
@@ -6,9 +6,9 @@ from pyramid.util import is_nonstr_iter
 def url_quote(val, safe=''):  # bw compat api
     cls = val.__class__
     if cls is str:
-        val = val.encode('utf-8')
+        val = val.encode('utf-8', errors='surrogatepass').decode('utf-8', errors='replace').encode('utf-8')
     elif cls is not bytes:
-        val = str(val).encode('utf-8')
+        val = str(val).encode('utf-8', errors='surrogatepass').decode('utf-8', errors='replace').encode('utf-8')
     return _url_quote(val, safe=safe)
 
 
@@ -16,9 +16,9 @@ def url_quote(val, safe=''):  # bw compat api
 def quote_plus(val, safe=''):
     cls = val.__class__
     if cls is str:
-        val = val.encode('utf-8')
+        val = val.encode('utf-8', errors='surrogatepass').decode('utf-8', errors='replace').encode('utf-8')
     elif cls is not bytes:
-        val = str(val).encode('utf-8')
+        val = str(val).encode('utf-8', errors='surrogatepass').decode('utf-8', errors='replace').encode('utf-8')
     return _quote_plus(val, safe=safe)
```

Alternative fix: Use `errors='replace'` or `errors='ignore'` when encoding to replace surrogates with replacement character or skip them entirely.