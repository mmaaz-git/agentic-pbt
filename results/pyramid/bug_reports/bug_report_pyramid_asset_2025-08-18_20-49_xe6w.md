# Bug Report: pyramid.asset Backslash Handling on Unix

**Target**: `pyramid.asset.abspath_from_asset_spec`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

On Unix systems, `abspath_from_asset_spec` incorrectly treats a single backslash `\` as an absolute path, causing it to raise a ValueError even though backslash is not a path separator on Unix.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import pyramid.asset as asset

@given(st.just('\\'))
def test_backslash_handling(spec):
    """Backslash should not be treated as absolute path on Unix."""
    result = asset.abspath_from_asset_spec(spec, '__main__')
    assert result is not None
```

**Failing input**: `'\'`

## Reproducing the Bug

```python
import pyramid.asset as asset

result = asset.abspath_from_asset_spec('\\', '__main__')
# Raises: ValueError: Use of .. or absolute path in a resource path is not allowed.
```

## Why This Is A Bug

On Unix systems, backslash (`\`) is not a path separator - it's a regular character that can appear in filenames. The function incorrectly treats it as an absolute path marker, which causes pkg_resources to reject it. This prevents legitimate filenames containing backslashes from being processed on Unix systems.

## Fix

The issue lies in how pkg_resources validates paths. A workaround could be implemented in `abspath_from_asset_spec` to handle this edge case:

```diff
def abspath_from_asset_spec(spec, pname='__main__'):
    if pname is None:
        return spec
    pname, filename = resolve_asset_spec(spec, pname)
    if pname is None:
        return filename
+   # Handle single backslash on Unix - it's not an absolute path
+   if filename == '\\' and os.name != 'nt':
+       filename = './' + filename
    return pkg_resources.resource_filename(pname, filename)
```