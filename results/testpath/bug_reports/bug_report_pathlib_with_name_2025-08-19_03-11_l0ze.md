# Bug Report: pathlib.PurePath.with_name() Inconsistent Special Name Validation

**Target**: `pathlib.PurePath.with_name`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

`PurePath.with_name()` inconsistently validates special directory names - it correctly rejects `'.'` but incorrectly accepts `'..'`, despite both being special directory references in filesystems.

## Property-Based Test

```python
from pathlib import PurePath
import pytest
from hypothesis import given, strategies as st

@given(st.sampled_from(["", ".", "..", "/"]))
def test_with_name_invalid_inputs(invalid_name):
    """Test with_name with known invalid inputs."""
    base = PurePath("dir/file.txt")
    
    # These should all raise ValueError for consistency
    with pytest.raises(ValueError):
        base.with_name(invalid_name)
```

**Failing input**: `".."`

## Reproducing the Bug

```python
from pathlib import PurePath

base = PurePath("dir/file.txt")

try:
    base.with_name(".")
    print("'.' accepted")
except ValueError:
    print("'.' rejected (correct)")

try:
    result = base.with_name("..")
    print(f"'..' accepted: {result}")
except ValueError:
    print("'..' rejected")
```

## Why This Is A Bug

Both `'.'` and `'..'` are special directory names in filesystems:
- `'.'` refers to the current directory
- `'..'` refers to the parent directory

The method correctly rejects `'.'` as an invalid name, but inconsistently accepts `'..'`. This creates semantic confusion where `dir/..` could mean either "parent of dir" or "a file named '..' in dir". Since `with_name()` is meant to replace the filename component, accepting `'..'` violates the principle that special directory references should not be valid filenames.

## Fix

```diff
--- a/pathlib.py
+++ b/pathlib.py
@@ -356,7 +356,7 @@ class PurePath:
     def with_name(self, name):
         """Return a new path with the file name changed."""
-        if not name or '/' in name or (name == '.'):
+        if not name or '/' in name or name in ('.', '..'):
             raise ValueError(f"Invalid name {name!r}")
         return self._from_parsed_parts(self._drv, self._root,
                                         self._parts[:-1] + [name])