# Bug Report: urllib.request.parse_http_list Incorrectly Handles Escaped Backslashes

**Target**: `urllib.request.parse_http_list`
**Severity**: Medium  
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `parse_http_list` function incorrectly consumes backslashes that are followed by non-quote characters in quoted strings, violating RFC 2068 escaping rules.

## Property-Based Test

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=0, max_size=100))
def test_parse_http_list_quotes(content):
    quoted = f'"{content}"'
    result = urllib.request.parse_http_list(quoted)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == quoted
```

**Failing input**: `content='\'` (single backslash)

## Reproducing the Bug

```python
import urllib.request

input_str = '"\\"'  # Quoted string containing single backslash
result = urllib.request.parse_http_list(input_str)
print(f"Input: {repr(input_str)}")
print(f"Result: {result}")
print(f"Expected: ['\"\\\\\"']")
print(f"Actual: {result}")
```

## Why This Is A Bug

According to RFC 2068 and standard HTTP header parsing rules, inside quoted strings, a backslash should only escape the next character if that character is a quote or another backslash. A backslash followed by any other character should be preserved as-is. The current implementation incorrectly sets `escape=True` and skips the backslash regardless of what follows, causing data loss. When the input is `"\"`, the backslash is consumed and lost, resulting in `""` instead of `"\"`.

## Fix

```diff
--- a/urllib/request.py
+++ b/urllib/request.py
@@ -1424,8 +1424,11 @@ def parse_http_list(s):
             continue
         if quote:
             if cur == '\\':
-                escape = True
-                continue
+                # Only escape if next char is quote or backslash
+                if i + 1 < len(s) and s[i + 1] in ('"', '\\'):
+                    escape = True
+                    continue
+            part += cur
             elif cur == '"':
                 quote = False
             part += cur
```