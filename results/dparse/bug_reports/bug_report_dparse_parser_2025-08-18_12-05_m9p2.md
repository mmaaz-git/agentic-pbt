# Bug Report: dparse.parser.SetupCfgParser Typo in Option Name

**Target**: `dparse.parser.SetupCfgParser`  
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

SetupCfgParser looks for 'test_require' instead of the correct 'tests_require' option, causing it to miss test dependencies in setup.cfg files.

## Property-Based Test

```python
from hypothesis import given
from hypothesis import strategies as st

@given(st.lists(st.text(min_size=1), min_size=1))
def test_setup_cfg_parser_finds_tests_require(packages):
    """SetupCfgParser should find dependencies in tests_require section"""
    content = f"""
[options]
tests_require = 
    {chr(10).join(packages)}
"""
    
    from dparse.dependencies import DependencyFile
    from dparse import filetypes
    
    # Assuming the first bug is fixed
    dep_file = DependencyFile(content=content, file_type=filetypes.setup_cfg)
    dep_file.parse()
    
    # Should find the test dependencies
    assert len(dep_file.dependencies) == len(packages)
```

**Failing input**: Any setup.cfg with `tests_require` section

## Reproducing the Bug

```python
from configparser import ConfigParser

# Demonstrate the standard setuptools option name
setup_cfg = """
[options]
tests_require = 
    pytest>=7.0.0
    mock>=4.0.0
"""

parser = ConfigParser()
parser.read_string(setup_cfg)

# Standard setuptools uses 'tests_require' (with 's')
assert parser.has_option('options', 'tests_require') == True
assert parser.has_option('options', 'test_require') == False

# But dparse looks for 'test_require' (without 's') on line 417
# This means test dependencies are never parsed
```

## Why This Is A Bug

The bug is a typo in line 417 of SetupCfgParser where it looks for 'test_require' instead of 'tests_require'. This is inconsistent with:
1. Standard setuptools configuration which uses 'tests_require'
2. The plural form used in other options like 'install_requires' and 'setup_requires'

As a result, test dependencies specified in setup.cfg files are silently ignored.

## Fix

```diff
--- a/dparse/parser.py
+++ b/dparse/parser.py
@@ -414,7 +414,7 @@ class SetupCfgParser(Parser):
         parser.read_string(self.obj.content)
         for section in parser.sections():
             if section == 'options':
-                options = 'install_requires', 'setup_requires', 'test_require'
+                options = 'install_requires', 'setup_requires', 'tests_require'
                 for name in options:
                     if parser.has_option('options', name):
                         content = parser.get('options', name)
```