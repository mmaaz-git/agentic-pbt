# Bug Report: Flask/Werkzeug Request Silently Strips Whitespace from URL Paths

**Target**: `flask.Request` / `werkzeug.test.EnvironBuilder`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

Flask/Werkzeug's Request object silently strips tab (\t), newline (\n), and carriage return (\r) characters from URL paths while preserving spaces and other special characters, creating inconsistent behavior.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from werkzeug.test import EnvironBuilder
from flask import Request

@given(
    path=st.text(min_size=1, max_size=100).filter(lambda x: not any(c in x for c in ['\0']))
)
def test_request_path_preservation(path):
    """Test that Request preserves the exact path given"""
    if not path.startswith('/'):
        path = '/' + path
    
    builder = EnvironBuilder(path=path)
    env = builder.get_environ()
    request = Request(env)
    
    # Property: The path should be preserved exactly
    assert request.path == path
```

**Failing input**: `path='\t'`

## Reproducing the Bug

```python
from werkzeug.test import EnvironBuilder
from flask import Request

test_paths = [
    '/\t',           # Tab character
    '/test\ttab',    # Tab in middle
    '/test\nline',   # Newline
    '/test\rreturn', # Carriage return
    '/test space',   # Space (NOT stripped - inconsistent!)
]

for path in test_paths:
    builder = EnvironBuilder(path=path)
    env = builder.get_environ()
    request = Request(env)
    
    if request.path != path:
        print(f"Path changed: {repr(path)} -> {repr(request.path)}")
    else:
        print(f"Path preserved: {repr(path)}")
```

Output:
```
Path changed: '/\t' -> '/'
Path changed: '/test\ttab' -> '/testtab'
Path changed: '/test\nline' -> '/testline'  
Path changed: '/test\rreturn' -> '/testreturn'
Path preserved: '/test space'
```

## Why This Is A Bug

1. **Inconsistent behavior**: The code strips tabs, newlines, and carriage returns but preserves spaces and other whitespace like zero-width spaces. This inconsistency violates the principle of least surprise.

2. **Silent data modification**: The stripping happens silently without any warning or error, potentially causing data loss or security issues.

3. **URL encoding bypass**: URL-encoded tabs (%09) get decoded and then stripped, meaning `/test%09tab` becomes `/test	tab` which then becomes `/testtab`. This creates a situation where encoded and decoded URLs behave differently.

4. **Potential security implications**: Path-based routing or authentication that relies on exact path matching could be bypassed if whitespace is silently stripped.

## Fix

The fix would require modifying werkzeug's path normalization logic to either:
1. Preserve all whitespace characters consistently, or
2. Strip all whitespace characters consistently, or
3. Raise an error for paths containing problematic whitespace

The most backward-compatible fix would be option 1, treating all characters consistently without silent modification.