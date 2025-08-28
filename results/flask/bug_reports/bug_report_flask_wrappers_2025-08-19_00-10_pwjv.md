# Bug Report: flask.wrappers CORS Header Properties Incorrectly Parse String Inputs

**Target**: `flask.wrappers.Response` CORS-related header properties
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

Multiple CORS-related header properties in `flask.Response` incorrectly treat string inputs as character iterables instead of single values or comma-separated lists, causing each character to be treated as a separate item.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from flask import Response

@given(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5))
def test_response_access_control_allow_methods(methods):
    response = Response()
    
    # Set the methods as comma-separated string
    methods_str = ', '.join(methods)
    response.access_control_allow_methods = methods_str
    
    # Should be retrievable as the same value
    assert response.access_control_allow_methods == methods_str
    
    # Should be in headers
    assert response.headers.get('Access-Control-Allow-Methods') == methods_str
```

**Failing input**: `methods=['GET']` (or any single-element list)

## Reproducing the Bug

```python
from flask import Response

response = Response()
response.access_control_allow_methods = "GET"

print(f"Expected: HeaderSet(['GET'])")
print(f"Actual: {response.access_control_allow_methods}")
# Output: G, E, T

response2 = Response()
response2.access_control_allow_methods = "GET, POST"

print(f"\nExpected: HeaderSet(['GET', 'POST'])")  
print(f"Actual: {response2.access_control_allow_methods}")
# Output: G, E, T, ",", " ", P, O, S, T

response3 = Response()
response3.access_control_allow_headers = "Content-Type"
print(f"\nSame issue with access_control_allow_headers:")
print(f"Actual: {response3.access_control_allow_headers}")
# Output: C, o, n, t, e, n, t, -, T, y, p, e
```

## Why This Is A Bug

The setter for these properties treats string inputs as iterables of characters rather than as single header values or comma-separated lists. This violates the principle of least surprise - developers expect setting `"GET"` to result in a single method "GET", not three separate values "G", "E", "T".

The properties affected include:
- `access_control_allow_methods`
- `access_control_allow_headers`
- `access_control_expose_headers`

## Fix

The bug appears to be in how these properties handle string inputs. When a string is passed, it should either be treated as a single value or parsed as a comma-separated list, not iterated character by character. A high-level fix would involve checking if the input is a string and handling it appropriately before converting to a HeaderSet.

The current workaround is to always pass these values as lists:
```python
response.access_control_allow_methods = ["GET", "POST"]  # Works correctly
```

instead of:
```python
response.access_control_allow_methods = "GET, POST"  # Incorrectly parsed
```