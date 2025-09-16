# Bug Report: pydantic.networks URL Path Round-Trip Failure

**Target**: `pydantic.networks` - All URL types (HttpUrl, WebsocketUrl, FtpUrl, AnyUrl, etc.)
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

URL round-trip property is systematically violated for ALL path values across ALL URL types (HttpUrl, WebsocketUrl, FtpUrl, AnyUrl, etc.). The `build()` method always prepends an extra `/` to paths, making URLs non-reconstructible from their components.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from pydantic.networks import HttpUrl

@given(
    scheme=st.sampled_from(['http', 'https']),
    host=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=3, max_size=20)
)
@settings(max_examples=100)
def test_url_path_round_trip(scheme, host):
    original = HttpUrl.build(scheme=scheme, host=host, path=None)
    extracted_path = original.path
    rebuilt = HttpUrl.build(scheme=scheme, host=host, path=extracted_path)
    assert str(original) == str(rebuilt)
```

**Failing input**: `scheme='http', host='example', path=None`

## Reproducing the Bug

```python
from pydantic.networks import HttpUrl

# Test various path inputs
test_paths = [None, '', '/', '/path', 'path']

for path_input in test_paths:
    url1 = HttpUrl.build(scheme='http', host='example.com', path=path_input)
    path1 = url1.path
    
    url2 = HttpUrl.build(scheme='http', host='example.com', path=path1)
    path2 = url2.path
    
    print(f"Input: {path_input!r} -> URL1: {url1} (path={path1!r})")
    print(f"  Rebuild with {path1!r} -> URL2: {url2} (path={path2!r})")
    print(f"  Round-trip failed: {str(url1) != str(url2)}")

# Output:
# Input: None -> URL1: http://example.com/ (path='/')
#   Rebuild with '/' -> URL2: http://example.com// (path='//')
#   Round-trip failed: True
# Input: '' -> URL1: http://example.com/ (path='/')
#   Rebuild with '/' -> URL2: http://example.com// (path='//')
#   Round-trip failed: True
# Input: '/' -> URL1: http://example.com// (path='//')
#   Rebuild with '//' -> URL2: http://example.com/// (path='///')
#   Round-trip failed: True
# Input: '/path' -> URL1: http://example.com//path (path='//path')
#   Rebuild with '//path' -> URL2: http://example.com///path (path='///path')
#   Round-trip failed: True
# Input: 'path' -> URL1: http://example.com/path (path='/path')
#   Rebuild with '/path' -> URL2: http://example.com//path (path='//path')
#   Round-trip failed: True
```

## Why This Is A Bug

The URL build/extract round-trip property should hold: extracting components from a URL and rebuilding with those same components should produce an identical URL. This property is systematically violated:

1. **Every path gets an extra `/` prepended** when passed to `build()`
2. **The bug compounds** - each round-trip adds another slash (/ -> // -> /// -> ////)
3. **All path values are affected**, not just edge cases

This breaks fundamental expectations:
- URLs cannot be reliably serialized/deserialized through their components
- URL manipulation becomes unpredictable
- The `build()` method's behavior contradicts its purpose of constructing URLs from components

This affects any code that:
- Stores URL components in a database and reconstructs URLs
- Modifies URL components programmatically
- Implements URL routing or rewriting logic

## Fix

The issue appears to be in how the `build` method handles the path parameter. When a path of `/` is provided, it should not add an additional `/`. A potential fix would be to check if the path is already `/` and handle it specially:

```diff
# In the build method implementation
- path = path or '/'
+ if path is None:
+     path = '/'
+ elif path == '/':
+     path = ''  # Don't duplicate the root slash
```

Alternatively, the path property getter could be modified to return `None` or empty string for root paths to maintain round-trip compatibility.