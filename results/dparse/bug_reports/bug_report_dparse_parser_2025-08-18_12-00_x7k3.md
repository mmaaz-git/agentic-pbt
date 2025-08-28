# Bug Report: dparse.parser.SetupCfgParser AttributeError on String Section

**Target**: `dparse.parser.SetupCfgParser`
**Severity**: High
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

SetupCfgParser crashes with AttributeError when parsing any setup.cfg file due to incorrectly treating a string variable as an object with attributes.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from dparse.dependencies import DependencyFile
from dparse import filetypes

@given(st.text())
def test_setup_cfg_parser_doesnt_crash(content):
    """SetupCfgParser should handle any text content without AttributeError"""
    if "[options]" in content:
        dep_file = DependencyFile(
            content=content,
            file_type=filetypes.setup_cfg
        )
        dep_file.parse()  # Should not raise AttributeError
```

**Failing input**: Any input containing `[options]` section

## Reproducing the Bug

```python
from dparse.dependencies import DependencyFile
from dparse import filetypes

setup_cfg_content = """
[options]
install_requires = 
    requests>=2.28.0
"""

dep_file = DependencyFile(
    content=setup_cfg_content,
    file_type=filetypes.setup_cfg
)

dep_file.parse()  # Raises: AttributeError: 'str' object has no attribute 'name'
```

## Why This Is A Bug

The bug occurs in `SetupCfgParser.parse()` method where:
1. Line 416 attempts to access `section.name` but `section` is a string (from `parser.sections()`)
2. Line 420 attempts to call `section.get()` but `section` is a string, not the ConfigParser object

This makes SetupCfgParser completely unusable - it will crash on any valid setup.cfg file with an [options] section.

## Fix

```diff
--- a/dparse/parser.py
+++ b/dparse/parser.py
@@ -413,11 +413,11 @@ class SetupCfgParser(Parser):
         parser = ConfigParser()
         parser.read_string(self.obj.content)
         for section in parser.sections():
-            if section.name == 'options':
+            if section == 'options':
                 options = 'install_requires', 'setup_requires', 'test_require'
                 for name in options:
                     if parser.has_option('options', name):
-                        content = section.get('options', name)
+                        content = parser.get('options', name)
                         self._parse_content(content)
             elif section == 'options.extras_require':
                 for _, content in parser.items('options.extras_require'):
```