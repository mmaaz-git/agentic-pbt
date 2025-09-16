# Bug Report: isort.files.find Crashes on None Input

**Target**: `isort.files.find`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `files.find()` function crashes with a TypeError when None is present in the paths iterable, instead of handling it gracefully.

## Property-Based Test

```python
@given(st.lists(st.sampled_from([None]), min_size=1, max_size=5))
@settings(max_examples=10)
def test_none_in_paths(none_list: List):
    """Test how find handles None values in paths."""
    config = Config()
    skipped = []
    broken = []
    
    try:
        result = list(files.find(none_list, config, skipped, broken))
        assert isinstance(result, list)
    except (TypeError, AttributeError) as e:
        assert False, f"find() crashed on None input: {e}"
```

**Failing input**: `[None]`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort import files
from isort.settings import Config

config = Config()
skipped = []
broken = []

paths_with_none = [None]
result = list(files.find(paths_with_none, config, skipped, broken))
```

## Why This Is A Bug

The function should handle invalid inputs gracefully rather than crashing. When None is passed as a path, it should either skip it, add it to the broken list, or raise a more informative error. The current behavior results in a confusing TypeError from os.path.isdir().

## Fix

```diff
--- a/isort/files.py
+++ b/isort/files.py
@@ -12,6 +12,10 @@ def find(
     visited_dirs: Set[Path] = set()
 
     for path in paths:
+        if path is None:
+            broken.append(str(path))
+            continue
+            
         if os.path.isdir(path):
             for dirpath, dirnames, filenames in os.walk(
                 path, topdown=True, followlinks=config.follow_links
```