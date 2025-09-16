# Bug Report: urllib.request.parse_keqv_list IndexError on Empty Values

**Target**: `urllib.request.parse_keqv_list`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `parse_keqv_list` function crashes with IndexError when processing key=value pairs that have empty values (e.g., "key=").

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume

@given(st.text(min_size=0, max_size=50))
def test_parse_keqv_empty_value(key):
    assume('=' not in key)
    assume(key != '')
    
    case = f'{key}='  # Empty value
    result = urllib.request.parse_keqv_list([case])
    assert key in result
    assert result[key] == ''
```

**Failing input**: `key='0'` (or any valid key name)

## Reproducing the Bug

```python
import urllib.request

result = urllib.request.parse_keqv_list(['key='])
```

## Why This Is A Bug

The function is meant to parse key=value pairs from HTTP headers. Empty values are valid in HTTP headers (e.g., "Cookie: session="). The function correctly handles empty quoted values like `key=""` but crashes on unquoted empty values like `key=`. The crash occurs at line 1402 when checking `v[0]` on an empty string.

## Fix

```diff
--- a/urllib/request.py
+++ b/urllib/request.py
@@ -1399,7 +1399,7 @@ def parse_keqv_list(l):
     parsed = {}
     for elt in l:
         k, v = elt.split('=', 1)
-        if v[0] == '"' and v[-1] == '"':
+        if v and len(v) >= 2 and v[0] == '"' and v[-1] == '"':
             v = v[1:-1]
         parsed[k] = v
     return parsed
```