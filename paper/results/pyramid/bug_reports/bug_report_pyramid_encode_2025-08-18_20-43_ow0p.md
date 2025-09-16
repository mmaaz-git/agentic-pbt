# Bug Report: pyramid.encode Non-ASCII Safe Parameter Handling

**Target**: `pyramid.encode.url_quote` and `pyramid.encode.quote_plus`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `url_quote` and `quote_plus` functions in pyramid.encode fail to properly handle non-ASCII characters in the `safe` parameter, causing these characters to be encoded even when explicitly marked as safe.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyramid.encode import url_quote

@given(st.text(min_size=1), st.text())
def test_url_quote_safe_parameter(text, safe):
    """Test that url_quote respects the safe parameter."""
    result = url_quote(text, safe=safe)
    
    # Characters in safe should not be encoded
    for char in safe:
        if char in text:
            # The character should appear unencoded in result
            if char not in '%':
                assert char in result or char not in text
```

**Failing input**: `text='\x80', safe='\x80'`

## Reproducing the Bug

```python
from pyramid.encode import url_quote, quote_plus

# Test 1: url_quote with non-ASCII safe character
result = url_quote('€', safe='€')
print(f"url_quote('€', safe='€') = '{result}'")
print(f"Expected: '€' but got: '{result}'")

# Test 2: quote_plus with non-ASCII safe character  
result = quote_plus('ñ', safe='ñ')
print(f"quote_plus('ñ', safe='ñ') = '{result}'")
print(f"Expected: 'ñ' but got: '{result}'")
```

## Why This Is A Bug

The functions claim to respect the `safe` parameter to keep certain characters unencoded. However, when non-ASCII characters are specified as safe, they still get percent-encoded. This happens because:

1. The functions encode the input text to UTF-8 bytes
2. They pass the original `safe` string (not UTF-8 encoded) to urllib.parse.quote
3. urllib.parse.quote looks for byte sequences to keep safe, not Unicode characters
4. The multi-byte UTF-8 representation doesn't match the single-character safe string

## Fix

```diff
--- a/pyramid/encode.py
+++ b/pyramid/encode.py
@@ -6,10 +6,15 @@ from pyramid.util import is_nonstr_iter
 def url_quote(val, safe=''):  # bw compat api
     cls = val.__class__
     if cls is str:
         val = val.encode('utf-8')
     elif cls is not bytes:
         val = str(val).encode('utf-8')
+    
+    # Encode safe parameter to match the encoding of val
+    if isinstance(safe, str):
+        safe = safe.encode('utf-8')
+    
     return _url_quote(val, safe=safe)
 
 
@@ -17,10 +22,15 @@ def url_quote(val, safe=''):  # bw compat api
 def quote_plus(val, safe=''):
     cls = val.__class__
     if cls is str:
         val = val.encode('utf-8')
     elif cls is not bytes:
         val = str(val).encode('utf-8')
+    
+    # Encode safe parameter to match the encoding of val
+    if isinstance(safe, str):
+        safe = safe.encode('utf-8')
+    
     return _quote_plus(val, safe=safe)
```