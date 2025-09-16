# Bug Report: DependencyFile Serialization Round-Trip Failure

**Target**: `dparse.dependencies.DependencyFile`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `DependencyFile.deserialize()` method fails with a TypeError when attempting to deserialize data that was created by `DependencyFile.serialize()`, breaking the expected round-trip functionality.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import dparse.filetypes as filetypes
from dparse.dependencies import DependencyFile

@given(st.sampled_from([
    filetypes.requirements_txt,
    filetypes.conda_yml,
    filetypes.setup_cfg,
    filetypes.tox_ini,
    filetypes.pipfile,
    filetypes.pipfile_lock,
    filetypes.poetry_lock,
    filetypes.pyproject_toml
]))
def test_serialization_round_trip(file_type):
    content = ""
    original = DependencyFile(content=content, file_type=file_type, path="test.file")
    serialized = original.serialize()
    deserialized = DependencyFile.deserialize(serialized)
    assert deserialized.file_type == original.file_type
```

**Failing input**: `file_type='requirements.txt'`

## Reproducing the Bug

```python
import dparse.filetypes as filetypes
from dparse.dependencies import DependencyFile

content = ""
file_type = filetypes.requirements_txt

df = DependencyFile(content=content, file_type=file_type)
serialized = df.serialize()
deserialized = DependencyFile.deserialize(serialized)
```

## Why This Is A Bug

The `serialize()` method includes a 'resolved_dependencies' key in its output, but the `deserialize()` method passes all remaining dictionary keys to the `DependencyFile.__init__()` constructor, which doesn't accept a 'resolved_dependencies' parameter. This breaks the fundamental expectation that `deserialize(serialize(obj))` should work.

## Fix

```diff
--- a/dparse/dependencies.py
+++ b/dparse/dependencies.py
@@ -205,6 +205,7 @@ class DependencyFile:
         """
         dependencies = [Dependency.deserialize(dep) for dep in
                         d.pop("dependencies", [])]
+        d.pop("resolved_dependencies", None)  # Remove resolved_dependencies from dict
         instance = cls(**d)
         instance.dependencies = dependencies
         return instance
```