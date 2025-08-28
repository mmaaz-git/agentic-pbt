# Bug Report: pyramid.traversal Null Byte Security Vulnerability

**Target**: `pyramid.traversal.split_path_info`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `split_path_info` function preserves null bytes (`\x00`) in path segments, creating a potential security vulnerability that could enable path traversal attacks.

## Property-Based Test

```python
@given(st.text(alphabet=string.printable + '\x00', min_size=1, max_size=20))
@settings(max_examples=500)
def test_null_bytes_rejected(text):
    """Null bytes in paths should be rejected or sanitized"""
    if '\x00' in text:
        path = '/' + text
        result = traversal.split_path_info(path)
        
        for segment in result:
            assert '\x00' not in segment, f"Null byte preserved in segment: {segment!r}"
```

**Failing input**: `/foo\x00bar`, `/\x00`, `/test\x00/path`, `/safe/../\x00/etc/passwd`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')
import pyramid.traversal as traversal

test_paths = [
    '/foo\x00bar',
    '/\x00',
    '/test\x00/path',
    '/safe/../\x00/etc/passwd'
]

for path in test_paths:
    result = traversal.split_path_info(path)
    print(f"split_path_info({path!r}) = {result!r}")
    for segment in result:
        if '\x00' in segment:
            print(f"  NULL BYTE IN: {segment!r}")
```

## Why This Is A Bug

Null bytes in file paths are a well-known security vulnerability:
1. **Path Traversal**: Null bytes can terminate strings in C-based systems, allowing attackers to bypass path restrictions
2. **Security Bypass**: `/etc/passwd\x00.jpg` might bypass extension checks while accessing `/etc/passwd`
3. **Industry Standard**: Most web frameworks (Django, Rails, Express) reject null bytes in URLs
4. **Inconsistent Behavior**: Different parts of the system may interpret null-terminated strings differently

Example attack scenario:
- Input: `/safe/../\x00/etc/passwd`
- Result: `('\x00', 'etc', 'passwd')`
- Could potentially access system files

## Fix

```diff
def split_path_info(path):
+   # Reject paths containing null bytes
+   if '\x00' in path:
+       raise ValueError("Null bytes not allowed in path")
    
    path = path.strip('/')
    clean = []
    for segment in path.split('/'):
+       # Additional safety check
+       if '\x00' in segment:
+           raise ValueError("Null bytes not allowed in path segments")
        if not segment or segment == '.':
            continue
        elif segment == '..':
            if clean:
                del clean[-1]
        else:
            clean.append(segment)
    return tuple(clean)
```