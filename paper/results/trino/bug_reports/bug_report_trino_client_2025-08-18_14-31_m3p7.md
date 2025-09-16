# Bug Report: trino.client ValueError in get_roles_values

**Target**: `trino.client.get_roles_values`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `get_roles_values` function crashes with a ValueError when parsing header values that don't contain an equals sign, causing an unpacking error.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from trino.client import get_roles_values

@given(st.text(min_size=1, max_size=50).filter(lambda s: '=' not in s))
def test_roles_without_equals(value_without_equals):
    """Test that role values without equals signs are handled gracefully."""
    headers = {'X-Trino-Set-Role': value_without_equals}
    # This should either skip invalid values or raise a meaningful error
    result = get_roles_values(headers, 'X-Trino-Set-Role')
```

**Failing input**: `"roleonly"`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from trino.client import get_roles_values

# This will crash with ValueError: not enough values to unpack (expected 2, got 1)
headers = {'X-Trino-Set-Role': 'roleonly'}
result = get_roles_values(headers, 'X-Trino-Set-Role')
```

## Why This Is A Bug

The function assumes all role values follow the `catalog=role` format, but doesn't validate this assumption. When a value without an equals sign is encountered, the tuple unpacking `for k, v in (kv.split("=", 1) for kv in kvs if kv)` fails because `split("=", 1)` returns a single-element list that cannot be unpacked into two variables.

This is particularly problematic for role parsing where malformed headers from a server could cause client crashes rather than being handled gracefully.

## Fix

```diff
def get_roles_values(headers: CaseInsensitiveDict[str], header: str) -> List[Tuple[str, str]]:
    kvs = get_header_values(headers, header)
-    return [
-        (k.strip(), urllib.parse.unquote_plus(v.strip()))
-        for k, v in (kv.split("=", 1) for kv in kvs if kv)
-    ]
+    result = []
+    for kv in kvs:
+        if kv and '=' in kv:
+            k, v = kv.split("=", 1)
+            result.append((k.strip(), urllib.parse.unquote_plus(v.strip())))
+    return result
```