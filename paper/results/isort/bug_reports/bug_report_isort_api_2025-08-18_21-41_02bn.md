# Bug Report: isort.api sort_code_string Returns Empty String with show_diff

**Target**: `isort.api.sort_code_string`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `sort_code_string` function returns an empty string when `show_diff` parameter is set to True or a TextIO object, instead of returning the sorted code.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from io import StringIO
from isort.api import sort_code_string

@given(st.text())
def test_show_diff_consistency(code):
    sorted_normal = sort_code_string(code)
    diff_output = StringIO()
    sorted_with_diff = sort_code_string(code, show_diff=diff_output)
    assert sorted_normal == sorted_with_diff
```

**Failing input**: Any non-empty code string, e.g., `"import b\nimport a"`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from io import StringIO
from isort.api import sort_code_string

code = "import b\nimport a"

sorted_normal = sort_code_string(code)
print(f"Normal sort: {repr(sorted_normal)}")

diff_output = StringIO()
sorted_with_diff = sort_code_string(code, show_diff=diff_output)
print(f"With show_diff: {repr(sorted_with_diff)}")

assert sorted_normal == sorted_with_diff, "show_diff changes the return value!"
```

## Why This Is A Bug

The documentation states that `sort_code_string` returns "a new string with [imports] sorted". The `show_diff` parameter should only control whether a diff is shown, not affect the return value. Users expecting to get both the sorted code AND see the diff will instead get an empty string, breaking their code.

## Fix

The issue is in the `sort_stream` function. When `show_diff` is enabled, it returns early without writing to the output stream. The fix requires ensuring the sorted output is written to the output_stream even when show_diff is True:

```diff
--- a/isort/api.py
+++ b/isort/api.py
@@ -161,23 +161,25 @@ def sort_stream(
     extension = extension or (file_path and file_path.suffix.lstrip(".")) or "py"
     if show_diff:
         _output_stream = StringIO()
         _input_stream = StringIO(input_stream.read())
         changed = sort_stream(
             input_stream=_input_stream,
             output_stream=_output_stream,
             extension=extension,
             config=config,
             file_path=file_path,
             disregard_skip=disregard_skip,
             raise_on_skip=raise_on_skip,
             **config_kwargs,
         )
         _output_stream.seek(0)
         _input_stream.seek(0)
+        output_content = _output_stream.read()
+        _output_stream.seek(0)
         show_unified_diff(
             file_input=_input_stream.read(),
-            file_output=_output_stream.read(),
+            file_output=output_content,
             file_path=file_path,
             output=output_stream if show_diff is True else show_diff,
             color_output=config.color_output,
         )
+        output_stream.write(output_content)
         return changed
```