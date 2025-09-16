# Bug Report: copier._cli data_file_switch crashes on empty YAML files

**Target**: `copier._cli._Subcommand.data_file_switch`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `data_file_switch` method crashes with AttributeError when processing empty YAML files because `yaml.safe_load` returns None for empty files.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import tempfile
import yaml
import pytest
from copier._cli import _Subcommand

@given(st.none())
def test_data_file_switch_empty_yaml(yaml_content):
    subcommand = _Subcommand(executable="test")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        # Create empty file
        temp_path = f.name
    
    with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'items'"):
        subcommand.data_file_switch(temp_path)
```

**Failing input**: Empty YAML file

## Reproducing the Bug

```python
#!/usr/bin/env python3
import sys
import tempfile
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')
from copier._cli import _Subcommand

with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
    f.flush()
    subcommand = _Subcommand(executable="copier")
    subcommand.data_file_switch(f.name)
```

## Why This Is A Bug

Empty YAML files are valid and may be created accidentally or through file truncation. The program should handle empty configuration files gracefully instead of crashing. Users expect robust handling of edge cases in configuration file processing.

## Fix

```diff
--- a/copier/_cli.py
+++ b/copier/_cli.py
@@ -195,6 +195,9 @@ class _Subcommand(cli.Application):
         """
         with Path(path).open("rb") as f:
             file_updates: AnyByStrDict = yaml.safe_load(f)
+        
+        if file_updates is None:
+            file_updates = {}
 
         updates_without_cli_overrides = {
             k: v for k, v in file_updates.items() if k not in self.data
```