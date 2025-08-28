# Bug Report: sudachipy.command_line Silent Failure on Long Descriptions

**Target**: `sudachipy.command_line._command_build` and `sudachipy.command_line._command_user_build`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Dictionary build commands silently fail when descriptions exceed 255 bytes in UTF-8, printing a misleading "will be truncated" message but actually returning without building the dictionary.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import sudachipy.command_line as cmd_line

@given(st.text(min_size=256))
def test_description_handling(description):
    """
    Property: Descriptions > 255 bytes should either be truncated
    or cause an error, but dictionary building should not silently fail.
    """
    desc_bytes = len(description.encode("utf-8"))
    if desc_bytes > 255:
        # The function should either:
        # 1. Truncate the description and proceed
        # 2. Raise an error
        # But NOT: print a message and return without building
        result = build_with_description(description)
        assert result is not None  # Should not silently fail
```

**Failing input**: Any string with UTF-8 byte length > 255, e.g., `"A" * 256`

## Reproducing the Bug

```python
import sys
import tempfile
import argparse
from pathlib import Path
from unittest import mock

sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')
import sudachipy.command_line as cmd_line

description = "A" * 256  # 256 bytes, just over the limit

args = argparse.Namespace(
    matrix_file="matrix.def",
    in_files=["input.csv"],
    out_file="output.dic",
    description=description,
    handler=cmd_line._command_build,
    print_usage=lambda: None
)

with tempfile.TemporaryDirectory() as tmpdir:
    matrix_file = Path(tmpdir) / "matrix.def"
    matrix_file.write_text("0 0 0")
    in_file = Path(tmpdir) / "input.csv"
    in_file.write_text("test,0,0,0,テスト,*,*,*,*,*,*,*,*")
    
    args.matrix_file = str(matrix_file)
    args.in_files = [str(in_file)]
    args.out_file = str(Path(tmpdir) / "output.dic")
    
    with mock.patch('sudachipy.sudachipy.build_system_dic') as mock_build:
        mock_build.return_value = []
        result = cmd_line._command_build(args, lambda: None)
        
        print(f"Function returned: {result}")  # Returns None
        print(f"Dictionary built: {mock_build.called}")  # False - never called!
```

## Why This Is A Bug

The code prints "Description is longer than 255 bytes in utf-8, it will be truncated" but then immediately returns without truncating or building the dictionary. This violates the principle of least surprise - users expect either successful execution (with truncation) or a clear error, not a silent failure with a misleading message.

## Fix

```diff
--- a/sudachipy/command_line.py
+++ b/sudachipy/command_line.py
@@ -153,8 +153,9 @@ def _command_build(args, print_usage):
 
     description = args.description or ""
     if len(description.encode("utf-8")) > 255:
-        print("Description is longer than 255 bytes in utf-8, it will be truncated")
-        return
+        print("Warning: Description is longer than 255 bytes in utf-8, truncating to 255 bytes", file=sys.stderr)
+        # Truncate to 255 bytes while maintaining valid UTF-8
+        description = description.encode("utf-8")[:255].decode("utf-8", errors="ignore")
 
     stats = sudachipy.build_system_dic(
         matrix=matrix,
@@ -190,8 +191,9 @@ def _command_user_build(args, print_usage):
 
     description = args.description or ""
     if len(description.encode("utf-8")) > 255:
-        print("Description is longer than 255 bytes in utf-8, it will be truncated")
-        return
+        print("Warning: Description is longer than 255 bytes in utf-8, truncating to 255 bytes", file=sys.stderr)
+        # Truncate to 255 bytes while maintaining valid UTF-8
+        description = description.encode("utf-8")[:255].decode("utf-8", errors="ignore")
 
     stats = sudachipy.build_user_dic(
         system=system,
```