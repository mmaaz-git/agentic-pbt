# Bug Report: google.auth._helpers.update_query Non-Idempotent Behavior

**Target**: `google.auth._helpers.update_query`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `update_query` function is not idempotent when updating URLs with certain query parameters, particularly those with empty values. Applying the same update twice can produce different URLs due to parameter reordering.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from google.auth import _helpers

urls_with_params = st.builds(
    lambda base, params: (base, params),
    base=st.sampled_from([
        "http://example.com",
        "https://example.com/path",
        "http://example.com?existing=param",
        "https://example.com/path?a=1&b=2"
    ]),
    params=st.dictionaries(
        st.text(alphabet=st.characters(blacklist_characters='&=?#'), min_size=1),
        st.text(min_size=0),
        min_size=0,
        max_size=5
    )
)

@given(urls_with_params)
@settings(max_examples=500)
def test_update_query_idempotence(url_and_params):
    """Test that update_query is idempotent: f(f(x)) == f(x)."""
    url, params = url_and_params
    
    if not params:
        return
    
    # Apply update once
    updated_once = _helpers.update_query(url, params)
    
    # Apply update again with same params
    updated_twice = _helpers.update_query(updated_once, params)
    
    # Should be the same (idempotent)
    assert updated_once == updated_twice
```

**Failing input**: `('http://example.com', {'00': '', '0': '0'})`

## Reproducing the Bug

```python
from google.auth import _helpers

url = 'http://example.com'
params = {'00': '', '0': '0'}

updated_once = _helpers.update_query(url, params)
print(f"First update:  {updated_once}")

updated_twice = _helpers.update_query(updated_once, params)
print(f"Second update: {updated_twice}")

assert updated_once == updated_twice, f"Not idempotent: {updated_once} != {updated_twice}"
```

## Why This Is A Bug

The function violates the mathematical property of idempotence (f(f(x)) = f(x)). The root cause is a type inconsistency in the implementation:

1. `urllib.parse.parse_qs()` returns values as lists (e.g., `{'0': ['0']}`)
2. The function updates with new params as strings (e.g., `{'0': '0'}`)
3. After `dict.update()`, values have mixed types which causes `urlencode()` to produce different parameter orderings

Additionally, `parse_qs` drops empty-valued parameters (e.g., `00=` is not parsed), causing them to be re-added in different positions.

## Fix

```diff
--- a/google/auth/_helpers.py
+++ b/google/auth/_helpers.py
@@ -213,7 +213,12 @@ def update_query(url, params, remove=None):
     parts = urllib.parse.urlparse(url)
     # Parse the query string.
     query_params = urllib.parse.parse_qs(parts.query)
-    # Update the query parameters with the new parameters.
+    # Convert new params to lists to match parse_qs format
+    params_as_lists = {}
+    for key, value in params.items():
+        if not isinstance(value, list):
+            value = [value] if value else []
+        params_as_lists[key] = value
+    # Update the query parameters with the new parameters.
-    query_params.update(params)
+    query_params.update(params_as_lists)
     # Remove any values specified in remove.
```