# Bug Report: flask.abort() Raises LookupError for Non-Error HTTP Status Codes

**Target**: `flask.abort`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

flask.abort() raises LookupError for valid HTTP status codes outside the 4xx and 5xx ranges, despite documentation suggesting it should work for any status code.

## Property-Based Test

```python
@given(st.integers(100, 599))
def test_flask_abort_status_codes(status_code):
    """Test that flask.abort raises correct HTTP exceptions"""
    from werkzeug.exceptions import HTTPException
    
    try:
        flask.abort(status_code)
        assert False, "abort should have raised an exception"
    except HTTPException as e:
        # Should have the correct status code
        if hasattr(e, 'code'):
            assert e.code == status_code or (status_code not in range(100, 600) and e.code in [500, 404])
```

**Failing input**: `100`

## Reproducing the Bug

```python
import flask

# Error status codes work as expected
try:
    flask.abort(404)
except Exception as e:
    print(f"404: {type(e).__name__}")  # Output: NotFound

# Non-error status codes raise LookupError
try:
    flask.abort(200)
except LookupError as e:
    print(f"200: {e}")  # Output: no exception for 200

try:
    flask.abort(100)
except LookupError as e:
    print(f"100: {e}")  # Output: no exception for 100
```

## Why This Is A Bug

The flask.abort() documentation states: "Raise an HTTPException for the given status code" without specifying that only error status codes (4xx and 5xx) are supported. Valid HTTP status codes like 100 (Continue), 200 (OK), and 301 (Moved Permanently) cause LookupError instead of raising an appropriate HTTPException or working as documented.

This violates the API contract implied by the documentation, which suggests any valid HTTP status code should work.

## Fix

The issue is primarily a documentation bug. The fix should clarify the intended behavior:

```diff
def abort(code: int | Response, *args: t.Any, **kwargs: t.Any) -> t.NoReturn:
    """Raise an :exc:`~werkzeug.exceptions.HTTPException` for the given
    status code.
+
+   Only error status codes (4xx and 5xx) are supported. Other status
+   codes (1xx, 2xx, 3xx) will raise LookupError as they are not
+   intended for aborting request processing.

    If :data:`~flask.current_app` is available, it will call its
    :attr:`~flask.Flask.aborter` object, otherwise it will use
    :func:`werkzeug.exceptions.abort`.

    :param code: The status code for the exception, which must be
-       registered in ``app.aborter``.
+       registered in ``app.aborter`` (typically 4xx or 5xx codes).
    :param args: Passed to the exception.
    :param kwargs: Passed to the exception.
```

Alternatively, Flask could handle non-error codes more gracefully by raising a more descriptive error message or supporting all status codes with appropriate exceptions.