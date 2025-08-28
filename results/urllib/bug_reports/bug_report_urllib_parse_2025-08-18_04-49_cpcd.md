# Bug Report: urllib.parse Round-Trip Failure with Whitespace in Netloc

**Target**: `urllib.parse.urlparse` and `urllib.parse.urlunparse`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `urlparse`/`urlunparse` round-trip fails when the netloc component contains certain whitespace characters (`\n`, `\r`, `\t`), as these characters are silently removed during parsing, violating the expected round-trip property.

## Property-Based Test

```python
import urllib.parse
from hypothesis import given, strategies as st

@given(st.sampled_from(['\n', '\r', '\t', '\r\n']))
def test_urlunparse_urlparse_round_trip_whitespace_netloc(char):
    original_components = ('http', char, '/path', '', '', '')
    url = urllib.parse.urlunparse(original_components)
    parsed = urllib.parse.urlparse(url)
    assert parsed.netloc == char
```

**Failing input**: `char='\n'` (also fails with `'\r'`, `'\t'`, `'\r\n'`)

## Reproducing the Bug

```python
import urllib.parse

# Create URL components with newline in netloc
components = ('http', '\n', '/path', '', '', '')

# Unparse to create URL string
url = urllib.parse.urlunparse(components)
print(f"Created URL: {repr(url)}")  # 'http://\n/path'

# Parse the URL back
parsed = urllib.parse.urlparse(url)
print(f"Parsed netloc: {repr(parsed.netloc)}")  # ''

# The netloc has been silently removed
assert parsed.netloc == '\n'  # AssertionError: '' != '\n'
```

## Why This Is A Bug

This violates the fundamental round-trip property that `urlparse(urlunparse(components))` should return the original components. While removing these characters may be intentional for security/normalization per the WHATWG spec, it creates an inconsistency where:

1. `urlunparse` accepts these characters in the netloc component
2. `urlparse` silently removes them without warning
3. This breaks the expectation that parsing and unparsing are inverse operations

The issue stems from `/home/linuxbrew/.linuxbrew/Cellar/python@3.13/3.13.6/lib/python3.13/urllib/parse.py:498` where `_UNSAFE_URL_BYTES_TO_REMOVE` (`['\t', '\r', '\n']`) are removed from the URL during parsing.

## Fix

The bug could be fixed by either:

1. **Option 1**: Have `urlunparse` reject or sanitize these characters upfront to maintain consistency
2. **Option 2**: Document this behavior clearly as a known limitation of the round-trip property
3. **Option 3**: Preserve these characters during parsing (may have security implications)

A potential fix for Option 1:

```diff
def urlunparse(components):
    """Put a parsed URL back together again.  This may result in a
    slightly different, but equivalent URL, if the URL that was parsed
    originally had redundant delimiters, e.g. a ? with an empty query
    (the draft states that these are equivalent)."""
    scheme, netloc, url, params, query, fragment, _coerce_result = (
                                                  _coerce_args(*components))
+   # Remove unsafe bytes that would be stripped during parsing
+   for b in ['\t', '\r', '\n']:
+       netloc = netloc.replace(b, '')
    if params:
        url = "%s;%s" % (url, params)
    return _coerce_result(urlunsplit((scheme, netloc, url, query, fragment)))
```