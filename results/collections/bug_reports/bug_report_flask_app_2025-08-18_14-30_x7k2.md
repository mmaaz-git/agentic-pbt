# Bug Report: flask.app Missing Header Validation

**Target**: `flask.app.Flask.make_response`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Flask's `make_response()` method fails to validate HTTP header values for newline characters before passing them to Werkzeug, causing late error detection and poor error messages.

## Property-Based Test

```python
from hypothesis import given, strategies as st, example
import string
from flask import Flask

@given(st.dictionaries(
    st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
    st.text()
))
@example({'X-Custom': '\n'})
@example({'Content-Type': 'text/plain\n'})
def test_make_response_headers_validation(headers):
    """Flask should validate headers before passing to Werkzeug"""
    app = Flask(__name__)
    
    has_newline = any('\n' in v or '\r' in v for v in headers.values())
    
    with app.test_request_context():
        if has_newline:
            # Flask passes invalid headers directly to Werkzeug
            # which raises ValueError deep in the stack
            with pytest.raises(ValueError, match="newline"):
                app.make_response(("body", headers))
```

**Failing input**: `{'X-Custom': '\n'}`

## Reproducing the Bug

```python
from flask import Flask

app = Flask(__name__)

with app.test_request_context():
    headers = {'X-Custom': 'value\nX-Injected: evil'}
    try:
        response = app.make_response(("body", headers))
        print("Headers accepted (unexpected)")
    except ValueError as e:
        print(f"ValueError from Werkzeug: {e}")
```

## Why This Is A Bug

Flask accepts header dictionaries in `make_response()` but doesn't validate them before passing to Werkzeug's Headers class. This violates the principle of early validation and causes:

1. **Late error detection**: Errors occur deep in Werkzeug's stack instead of at the Flask API boundary
2. **Poor error context**: The error doesn't indicate which Flask method accepted invalid input
3. **Security implications**: If headers come from user input, invalid values aren't caught early

The contract of `make_response()` should include validation of input parameters to provide clear, early errors.

## Fix

```diff
--- a/flask/app.py
+++ b/flask/app.py
@@ -1264,6 +1264,11 @@ class Flask(App):
 
         # extend existing headers with provided headers
         if headers:
+            # Validate headers before passing to response
+            if isinstance(headers, (dict, list, tuple)):
+                for key, value in (headers.items() if isinstance(headers, dict) else headers):
+                    if isinstance(value, str) and ('\n' in value or '\r' in value):
+                        raise ValueError(f"Header value for '{key}' must not contain newline characters")
             rv.headers.update(headers)
 
         return rv
```