# Bug Report: isort.settings Error Message Formatting with Special Characters

**Target**: `isort.settings.Config`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The Config class in isort.settings produces malformed error messages when py_version contains special characters like newlines, tabs, or carriage returns, making error messages difficult to read.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from isort.settings import Config, VALID_PY_TARGETS
import pytest

@given(st.text())
def test_py_version_validation(py_version):
    """Test that Config only accepts valid Python versions."""
    if py_version == "auto" or py_version in VALID_PY_TARGETS:
        config = Config(py_version=py_version)
        if py_version != "all" and py_version != "auto":
            assert config.py_version == f"py{py_version}"
    else:
        with pytest.raises(ValueError, match="The python version .* is not supported"):
            Config(py_version=py_version)
```

**Failing input**: `"\n"`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages")
from isort.settings import Config

config = Config(py_version="\n")
```

## Why This Is A Bug

When invalid py_version values containing special characters are provided, the error message directly includes these characters without proper representation. This results in error messages that are difficult to read and parse. For example, with py_version="\n", the error message literally contains a newline in the middle of the sentence, breaking the formatting.

## Fix

```diff
--- a/isort/settings.py
+++ b/isort/settings.py
@@ -256,7 +256,7 @@ class _Config:
 
         if py_version not in VALID_PY_TARGETS:
             raise ValueError(
-                f"The python version {py_version} is not supported. "
+                f"The python version {py_version!r} is not supported. "
                 "You can set a python version with the -py or --python-version flag. "
                 f"The following versions are supported: {VALID_PY_TARGETS}"
             )
```