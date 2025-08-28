# Bug Report: isort.core._indented_config Fails to Modify Config When Indent is Empty

**Target**: `isort.core._indented_config`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `_indented_config()` function returns the original unmodified config when given an empty string as indent, instead of returning a new config with `lines_after_imports=1` as intended.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from isort.settings import Config
import isort.core

@given(
    st.text(alphabet=" \t", min_size=0, max_size=10),
    st.integers(min_value=0, max_value=120)
)
def test_indented_config_line_length(indent, line_length):
    config = Config(line_length=line_length)
    indented = isort.core._indented_config(config, indent)
    
    # Should always set lines_after_imports=1 for indented configs
    assert indented.lines_after_imports == 1
```

**Failing input**: `indent=""`, `line_length=0`

## Reproducing the Bug

```python
from isort.settings import Config
import isort.core

config = Config(line_length=0)
indented = isort.core._indented_config(config, "")

print(f"Original lines_after_imports: {config.lines_after_imports}")
print(f"Indented lines_after_imports: {indented.lines_after_imports}")

assert indented.lines_after_imports == 1, "Should set lines_after_imports=1"
```

## Why This Is A Bug

The function's purpose is to create a modified configuration for indented code blocks. According to the code at line 501, it should always set `lines_after_imports=1` when creating the new config. However, when indent is empty, it returns the original config unchanged (line 495), bypassing the intended modifications.

## Fix

```diff
--- a/isort/core.py
+++ b/isort/core.py
@@ -492,9 +492,6 @@ def _has_changed(before: str, after: str, line_separator: str, ignore_whitespac
 
 
 def _indented_config(config: Config, indent: str) -> Config:
-    if not indent:
-        return config
-
     return Config(
         config=config,
         line_length=max(config.line_length - len(indent), 0),
```