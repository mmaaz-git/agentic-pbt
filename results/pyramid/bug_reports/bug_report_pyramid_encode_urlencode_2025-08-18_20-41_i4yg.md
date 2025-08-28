# Bug Report: pyramid.encode.urlencode Documentation/Contract Violation

**Target**: `pyramid.encode.urlencode`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The documentation for `pyramid.encode.urlencode` states that None values are "dropped from the resulting output", but the implementation actually includes them as `key=` (key with empty value).

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyramid import encode

@given(
    st.dictionaries(
        st.text(min_size=1),
        st.one_of(st.none(), st.text(), st.integers())
    )
)
def test_urlencode_none_values(data):
    """Test that None values in urlencode are handled as documented."""
    result = encode.urlencode(data)
    
    for key, value in data.items():
        if value is None:
            # According to v1.5 docs, None values should be "dropped"
            # But implementation produces "key=" 
            encoded_key = encode.quote_plus(key)
            assert f"{encoded_key}=" in result
```

**Failing input**: Any dictionary with None values, e.g., `{'key': None}`

## Reproducing the Bug

```python
from pyramid import encode

# Test case 1: Single None value
result1 = encode.urlencode({'key': None})
print(f"urlencode({{'key': None}}): {result1!r}")
# Expected per docs: '' (dropped)
# Actual: 'key='

# Test case 2: None with other values
result2 = encode.urlencode({'a': None, 'b': 'value'})
print(f"urlencode({{'a': None, 'b': 'value'}}): {result2!r}")
# Expected per docs: 'b=value' (a dropped)
# Actual: 'a=&b=value'

# Test case 3: Multiple None values
result3 = encode.urlencode([('a', None), ('b', None)])
print(f"urlencode([('a', None), ('b', None)]): {result3!r}")
# Expected per docs: '' (both dropped)
# Actual: 'a=&b='
```

## Why This Is A Bug

The docstring at lines 49-51 of `/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages/pyramid/encode.py` states:

> .. versionchanged:: 1.5
>    In a key/value pair, if the value is ``None`` then it will be
>    dropped from the resulting output.

This documentation suggests that key-value pairs with None values should be completely omitted from the output. However, the implementation at lines 75-76 produces `key=` (key with empty value) instead of dropping the pair entirely. This is a contract violation where the implementation doesn't match the documented behavior.

## Fix

Either update the documentation to match the implementation, or change the implementation to match the documentation. To fix the documentation:

```diff
--- a/pyramid/encode.py
+++ b/pyramid/encode.py
@@ -48,8 +48,8 @@ def urlencode(query, doseq=True, quote_via=quote_plus):
 
     .. versionchanged:: 1.5
-       In a key/value pair, if the value is ``None`` then it will be
-       dropped from the resulting output.
+       In a key/value pair, if the value is ``None`` then it will be
+       rendered as ``key=`` (key with empty value) in the resulting output.
 
     .. versionchanged:: 1.9
```

Alternatively, to fix the implementation to match the documentation:

```diff
--- a/pyramid/encode.py
+++ b/pyramid/encode.py
@@ -73,8 +73,7 @@ def urlencode(query, doseq=True, quote_via=quote_plus):
                 result += '%s%s=%s' % (prefix, k, x)
                 prefix = '&'
         elif v is None:
-            result += '%s%s=' % (prefix, k)
+            continue  # Drop None values as documented
         else:
             v = quote_via(v)
             result += '%s%s=%s' % (prefix, k, v)
```