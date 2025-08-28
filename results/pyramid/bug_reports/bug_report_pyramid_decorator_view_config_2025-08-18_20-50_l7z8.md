# Bug Report: pyramid_decorator view_config JSON Renderer Fails to Encode Strings

**Target**: `pyramid_decorator.view_config`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `view_config` decorator with `renderer='json'` fails to properly JSON-encode string return values, producing invalid JSON output that cannot be parsed.

## Property-Based Test

```python
@given(
    value=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.lists(st.integers() | st.text(), max_size=10),
        st.dictionaries(st.text(), st.integers() | st.text(), max_size=10)
    )
)
def test_view_config_json_roundtrip(value):
    """Property: JSON renderer should produce parseable JSON that round-trips."""
    
    @pyramid_decorator.view_config(renderer='json')
    def view_func():
        return value
    
    result = view_func()
    assert isinstance(result, str)
    parsed = json.loads(result)
    assert parsed == value
```

**Failing input**: `value=''`

## Reproducing the Bug

```python
import json
import pyramid_decorator

@pyramid_decorator.view_config(renderer='json')
def view_func():
    return ''

result = view_func()
parsed = json.loads(result)
```

## Why This Is A Bug

The `renderer='json'` option should ensure that all return values are properly JSON-encoded. However, when the return value is already a string, the code at line 99-100 checks `if not isinstance(result, str)` before calling `json.dumps()`. This means string values are returned as-is without JSON encoding, violating the JSON format specification. An empty string `''` is not valid JSON (should be `""`), and text like `'hello'` is also invalid JSON (should be `"hello"`).

## Fix

```diff
--- a/pyramid_decorator.py
+++ b/pyramid_decorator.py
@@ -96,8 +96,7 @@ def view_config(**settings) -> Callable[[F], F]:
             renderer = settings.get('renderer')
             if renderer == 'json':
                 import json
-                if not isinstance(result, str):
-                    result = json.dumps(result)
+                result = json.dumps(result)
             elif renderer == 'string':
                 result = str(result)
```