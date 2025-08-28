# Bug Report: flask.json.dumps Does Not Sort Keys Without App Context

**Target**: `flask.json.dumps`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

`flask.json.dumps()` fails to sort dictionary keys when called without an active Flask application context, violating the expected behavior that Flask's JSON serialization should always sort keys by default as specified in `DefaultJSONProvider.sort_keys = True`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import flask.json
import json

@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-1e10, max_value=1e10),
            st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
            st.text(max_size=100)
        ),
        min_size=0,
        max_size=10
    )
)
def test_json_dumps_sorts_keys(data):
    encoded = flask.json.dumps(data)
    decoded = flask.json.loads(encoded)
    
    # Flask should sort keys by default (DefaultJSONProvider.sort_keys = True)
    standard_encoded = json.dumps(data, sort_keys=True)
    standard_decoded = json.loads(standard_encoded)
    assert list(decoded.keys()) == list(standard_decoded.keys())
```

**Failing input**: `{'0': None, '/': None}`

## Reproducing the Bug

```python
import flask.json

data = {'b': 1, 'a': 2, '0': 3, '/': 4}

flask_encoded = flask.json.dumps(data)
flask_decoded = flask.json.loads(flask_encoded)

print(f"Keys after flask.json.dumps/loads: {list(flask_decoded.keys())}")
print(f"Expected sorted keys: {sorted(data.keys())}")

assert list(flask_decoded.keys()) == sorted(data.keys()), "Keys should be sorted!"
```

## Why This Is A Bug

Flask's `DefaultJSONProvider` class explicitly sets `sort_keys = True` as a class attribute with documentation stating "Sort the keys in any serialized dicts." However, when `flask.json.dumps()` is called without an active application context, it falls back to the standard library's `json.dumps()` without passing `sort_keys=True`, resulting in inconsistent behavior. This violates the API contract that Flask's JSON operations should sort keys by default.

## Fix

```diff
--- a/flask/json/__init__.py
+++ b/flask/json/__init__.py
@@ -41,6 +41,7 @@ def dumps(obj: t.Any, **kwargs: t.Any) -> str:
         return current_app.json.dumps(obj, **kwargs)
 
     kwargs.setdefault("default", _default)
+    kwargs.setdefault("sort_keys", True)
     return _json.dumps(obj, **kwargs)
 
 
@@ -72,6 +73,7 @@ def dump(obj: t.Any, fp: t.IO[str], **kwargs: t.Any) -> None:
         current_app.json.dump(obj, fp, **kwargs)
     else:
         kwargs.setdefault("default", _default)
+        kwargs.setdefault("sort_keys", True)
         _json.dump(obj, fp, **kwargs)
```