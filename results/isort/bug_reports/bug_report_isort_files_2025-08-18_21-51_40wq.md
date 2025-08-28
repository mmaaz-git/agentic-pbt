# Bug Report: isort.files.find Crashes on Float Input

**Target**: `isort.files.find`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `files.find()` function crashes with a TypeError when float values are present in the paths iterable, failing to handle non-string types gracefully.

## Property-Based Test

```python
@given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1, max_size=5))
@settings(max_examples=10)
def test_float_in_paths(float_paths):
    """Test that find handles float values without crashing."""
    config = Config()
    skipped = []
    broken = []
    
    try:
        result = list(files.find(float_paths, config, skipped, broken))
        assert isinstance(result, list)
    except TypeError as e:
        if "float" in str(e):
            assert False, f"find() crashed on float input: {e}"
```

**Failing input**: `[0.0]` or any float value

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort import files
from isort.settings import Config

config = Config()
skipped = []
broken = []

paths_with_float = [3.14]
result = list(files.find(paths_with_float, config, skipped, broken))
```

## Why This Is A Bug

The function crashes when encountering float values in the paths iterable. While floats are not valid file paths, the function should handle them gracefully by either converting them to strings, skipping them, or adding them to the broken list, rather than crashing with an unhelpful TypeError from os.path.isdir().

## Fix

```diff
--- a/isort/files.py
+++ b/isort/files.py
@@ -12,6 +12,13 @@ def find(
     visited_dirs: Set[Path] = set()
 
     for path in paths:
+        if path is None or isinstance(path, float):
+            broken.append(str(path))
+            continue
+        
+        # Convert non-string types to strings
+        if not isinstance(path, (str, bytes, os.PathLike)):
+            path = str(path)
+            
         if os.path.isdir(path):
             for dirpath, dirnames, filenames in os.walk(
                 path, topdown=True, followlinks=config.follow_links
```