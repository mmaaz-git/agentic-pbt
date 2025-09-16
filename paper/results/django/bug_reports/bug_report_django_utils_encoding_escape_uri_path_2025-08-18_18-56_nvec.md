# Bug Report: django.utils.encoding.escape_uri_path Non-Idempotent Escaping

**Target**: `django.utils.encoding.escape_uri_path`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `escape_uri_path` function incorrectly re-escapes already-escaped URI paths, causing exponential growth of escape sequences when called multiple times.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import django.utils.encoding

@given(st.text())
def test_escape_uri_path_stability(text):
    """Test that escape_uri_path is stable when applied multiple times."""
    escaped_once = django.utils.encoding.escape_uri_path(text)
    escaped_twice = django.utils.encoding.escape_uri_path(escaped_once)
    escaped_thrice = django.utils.encoding.escape_uri_path(escaped_twice)
    assert escaped_twice == escaped_thrice, f"escape_uri_path not stable: {repr(text)}"
```

**Failing input**: `'%'`

## Reproducing the Bug

```python
import django.utils.encoding

# Case 1: Single percent sign
text = '%'
escaped_once = django.utils.encoding.escape_uri_path(text)
escaped_twice = django.utils.encoding.escape_uri_path(escaped_once)
print(f"Original: {text}")
print(f"Escaped once: {escaped_once}")   # Output: %25
print(f"Escaped twice: {escaped_twice}") # Output: %2525 (incorrect!)

# Case 2: Already-escaped path
path = '/test%20path'  # Path with escaped space
result = django.utils.encoding.escape_uri_path(path)
print(f"Already escaped path: {path}")
print(f"Double-escaped: {result}")  # Output: /test%2520path (incorrect!)

# Case 3: Exponential growth
input_str = '%'
for i in range(4):
    input_str = django.utils.encoding.escape_uri_path(input_str)
    print(f"Iteration {i+1}: {input_str}")
# Output shows exponential growth: %25, %2525, %252525, %25252525
```

## Why This Is A Bug

The function violates the idempotence property expected from escaping functions. When processing already-escaped URI paths (a common scenario in web applications), it incorrectly escapes the '%' character in escape sequences like '%20', producing invalid double-escaped paths. This can lead to:

1. Broken URLs when the function is called in multiple layers of code
2. Incorrect path interpretation when already-escaped paths are processed
3. Exponential string growth if called repeatedly

## Fix

The function should detect and preserve already-escaped sequences, or include '%' in the safe characters when the input already contains valid escape sequences. A potential fix:

```diff
def escape_uri_path(path):
    """
    Escape the unsafe characters from the path portion of a Uniform Resource
    Identifier (URI).
    """
-   return quote(path, safe="/:@&+$,-_.!~*'()")
+   # Include % in safe chars to preserve already-escaped sequences
+   # Or use quote(path, safe="/:@&+$,-_.!~*'()%")
+   # Or implement logic to detect and preserve valid escape sequences
+   import re
+   # Check if path already contains valid percent-encoded sequences
+   if re.search(r'%[0-9A-Fa-f]{2}', path):
+       # Path appears to be already escaped, preserve % signs
+       return quote(path, safe="/:@&+$,-_.!~*'()%")
+   else:
+       # Path is not escaped, escape everything including %
+       return quote(path, safe="/:@&+$,-_.!~*'()")
```