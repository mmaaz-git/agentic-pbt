# Bug Report: copier._cli data_switch crashes on arguments without equals sign

**Target**: `copier._cli._Subcommand.data_switch`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `data_switch` method crashes with ValueError when given command-line arguments that don't contain an equals sign, instead of providing a helpful error message.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from copier._cli import _Subcommand

@given(st.text())
def test_data_switch_parsing_invariant(value_string: str):
    subcommand = _Subcommand(executable="test")
    
    if "=" not in value_string:
        with pytest.raises(ValueError, match="not enough values to unpack"):
            subcommand.data_switch([value_string])
    else:
        subcommand.data_switch([value_string])
        key = value_string.split("=", 1)[0]
        value = value_string.split("=", 1)[1]
        assert subcommand.data[key] == value
```

**Failing input**: `"MY_VAR"` (any string without "=")

## Reproducing the Bug

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')
from copier._cli import _Subcommand

subcommand = _Subcommand(executable="copier")
subcommand.data_switch(["MY_VAR"])
```

## Why This Is A Bug

The CLI expects data arguments in "VARIABLE=VALUE" format. When users mistype or forget the equals sign, the program crashes with an unhelpful error instead of providing guidance. This violates user experience expectations for CLI tools, which should provide clear error messages for invalid input.

## Fix

```diff
--- a/copier/_cli.py
+++ b/copier/_cli.py
@@ -178,6 +178,9 @@ class _Subcommand(cli.Application):
                 Each value in the list is of the following form: `NAME=VALUE`.
         """
         for arg in values:
+            if "=" not in arg:
+                raise UserMessageError(
+                    f"Invalid data argument '{arg}'. Expected format: VARIABLE=VALUE")
             key, value = arg.split("=", 1)
             self.data[key] = value
```