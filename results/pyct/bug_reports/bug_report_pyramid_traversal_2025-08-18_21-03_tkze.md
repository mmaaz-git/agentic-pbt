# Bug Report: pyramid.traversal Invalid Percent Encoding Accepted

**Target**: `pyramid.traversal.traversal_path`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `traversal_path` function incorrectly accepts invalid percent-encoded sequences without raising `URLDecodeError`, violating URL encoding standards and its documented behavior.

## Property-Based Test

```python
@given(st.text(alphabet='%' + string.ascii_letters + string.digits, min_size=1, max_size=20))
@settings(max_examples=1000)
@example('%')
@example('%%')
@example('%G')
@example('%ZZ')
def test_invalid_percent_encoding_should_fail(text):
    """Invalid percent encoding should raise URLDecodeError"""
    import re
    invalid_pattern = re.compile(r'%(?![0-9A-Fa-f]{2})')
    
    if invalid_pattern.search(text):
        path = '/' + text
        try:
            result = traversal.traversal_path(path)
            assert False, f"Invalid encoding accepted: {text!r} -> {result}"
        except traversal.URLDecodeError:
            pass  # Expected behavior
```

**Failing input**: `%`, `%%`, `%G`, `%ZZ`, `%1`, `foo%`, etc.

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')
import pyramid.traversal as traversal

invalid_paths = ['/%', '/%%', '/%G', '/%ZZ', '/foo%1bar']
for path in invalid_paths:
    result = traversal.traversal_path(path)
    print(f"traversal_path('{path}') = {result}")
```

## Why This Is A Bug

URL percent-encoding requires `%` to be followed by exactly two hexadecimal digits. Invalid sequences should raise `URLDecodeError` as documented. Current behavior:
- Accepts malformed encodings like `%`, `%%`, `%G`
- Partially decodes invalid sequences (e.g., `%1` becomes `\x01`)
- Violates RFC 3986 URL encoding standards
- Could bypass security filters expecting proper validation

## Fix

The issue appears to be in how percent sequences are decoded. The function should validate that each `%` is followed by exactly 2 hex digits before attempting to decode:

```diff
# In the URL decoding logic
def decode_percent_sequence(text):
    import re
+   # Validate all percent sequences first
+   invalid = re.search(r'%(?![0-9A-Fa-f]{2})', text)
+   if invalid:
+       raise URLDecodeError('Invalid percent-encoding sequence')
    # Continue with decoding...
```