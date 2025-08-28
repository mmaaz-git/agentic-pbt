# Bug Report: trino.client ValueError in get_prepared_statement_values

**Target**: `trino.client.get_prepared_statement_values`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `get_prepared_statement_values` function crashes with a ValueError when parsing header values that don't contain an equals sign, causing an unpacking error.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from trino.client import get_prepared_statement_values

@given(st.text(min_size=1, max_size=50).filter(lambda s: '=' not in s))
def test_prepared_statement_without_equals(value_without_equals):
    """Test that prepared statement values without equals signs are handled gracefully."""
    headers = {'X-Trino-Added-Prepare': value_without_equals}
    # This should either skip invalid values or raise a meaningful error
    result = get_prepared_statement_values(headers, 'X-Trino-Added-Prepare')
```

**Failing input**: `"statementonly"`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from trino.client import get_prepared_statement_values

# This will crash with ValueError: not enough values to unpack (expected 2, got 1)
headers = {'X-Trino-Added-Prepare': 'statementonly'}
result = get_prepared_statement_values(headers, 'X-Trino-Added-Prepare')
```

## Why This Is A Bug

The function assumes all prepared statement values follow the `name=statement` format, but doesn't validate this assumption. When a value without an equals sign is encountered, the tuple unpacking `for k, v in (kv.split("=", 1) for kv in kvs if kv)` fails because `split("=", 1)` returns a single-element list that cannot be unpacked into two variables.

This could cause client crashes when processing malformed prepared statement headers from a server response.

## Fix

```diff
def get_prepared_statement_values(headers: CaseInsensitiveDict[str], header: str) -> List[Tuple[str, str]]:
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