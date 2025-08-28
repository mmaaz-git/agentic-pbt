# Bug Report: pathlib.PurePath.with_suffix() Crash on Double-Dot Filenames

**Target**: `pathlib.PurePath.with_suffix`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

`pathlib.PurePath.with_suffix('')` crashes with `ValueError` when called on filenames that start with two dots followed by text (e.g., "..file"), because it attempts to create an invalid filename consisting of just a single dot.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pathlib
import string

@given(st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=10))
def test_double_dot_pattern_crashes(suffix_text):
    filename = f"..{suffix_text}"
    p = pathlib.PurePath(filename)
    
    assert p.stem == "."
    assert p.suffix == f".{suffix_text}"
    
    try:
        p.with_suffix('')
        assert False, f"Expected crash for {filename}"
    except ValueError as e:
        assert "Invalid name '.'" in str(e)
```

**Failing input**: Any string matching pattern `"..[text]"` such as `"..file"`

## Reproducing the Bug

```python
import pathlib

p = pathlib.PurePath("..file")
print(f"Path: {p}")
print(f"  stem: {p.stem!r}")
print(f"  suffix: {p.suffix!r}")

result = p.with_suffix('')
```

## Why This Is A Bug

The bug occurs because:
1. pathlib parses "..file" as having stem="." and suffix=".file"
2. `with_suffix('')` attempts to reconstruct the filename as stem + new_suffix = "." + "" = "."
3. It then calls `with_name('.')` which raises `ValueError` because "." is not a valid filename

This violates the expected behavior that `with_suffix('')` should remove the suffix from any valid path. Users working with files that follow the "..file" naming pattern (which could occur in backup systems or special configurations) will encounter unexpected crashes.

## Fix

```diff
--- a/pathlib/_abc.py
+++ b/pathlib/_abc.py
@@ -231,6 +231,10 @@ class PurePathBase:
         if not suffix:
             stem = self.stem
             if not stem:
                 raise ValueError(f"{self!r} has an empty name")
+            # Special case: if stem is just "." and we're removing suffix,
+            # the result would be invalid. Keep original name instead.
+            if stem == "." and suffix == "":
+                return self
         elif suffix.startswith('.') and len(suffix) > 1:
             stem = self.stem
         else:
```

Alternatively, the parsing logic could be changed to not treat text after ".." as a suffix, which would prevent "..file" from being parsed as stem="." + suffix=".file" in the first place.