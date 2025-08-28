# Bug Report: urldecode JSON Fallback Broken for Simple Values

**Target**: `requests_oauthlib.oauth1_session.urldecode`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The urldecode function fails to parse simple JSON values (integers, strings, booleans) because they are incorrectly interpreted as URL-encoded data, preventing the JSON fallback from activating.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import json
from requests_oauthlib.oauth1_session import urldecode

@given(json_data=st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.text(min_size=1, max_size=10)
))
def test_urldecode_json_simple_values(json_data):
    """urldecode should parse simple JSON values correctly"""
    json_str = json.dumps(json_data)
    result = urldecode(json_str)
    assert result == json_data
```

**Failing input**: `0` (JSON integer)

## Reproducing the Bug

```python
from requests_oauthlib.oauth1_session import urldecode
import json

json_str = '0'
result = urldecode(json_str)
expected = json.loads(json_str)

print(f"Input: {json_str}")
print(f"Result: {result}")       
print(f"Expected: {expected}")   
```

## Why This Is A Bug

The docstring states "Parse query or json to python dictionary", implying the function should handle JSON data. However, simple JSON values like `0`, `true`, or `"text"` are incorrectly parsed as URL-encoded keys with empty values (e.g., `[('0', '')]`) instead of their JSON values. This breaks the dual-mode parsing promise and makes the function unreliable for JSON data that isn't a dictionary or array.

## Fix

```diff
--- a/requests_oauthlib/oauth1_session.py
+++ b/requests_oauthlib/oauth1_session.py
@@ -16,10 +16,17 @@ log = logging.getLogger(__name__)
 
 def urldecode(body):
     """Parse query or json to python dictionary"""
+    import json
+    
+    # Try JSON first for simple values
+    try:
+        return json.loads(body)
+    except (json.JSONDecodeError, TypeError):
+        pass
+    
+    # Fall back to URL decoding
     try:
         return _urldecode(body)
     except Exception:
-        import json
-
-        return json.loads(body)
+        # If both fail, raise the original JSON error
+        return json.loads(body)
```