# Bug Report: copier._subproject AttributeError on Non-Dict YAML

**Target**: `copier._subproject.Subproject.last_answers`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `Subproject.last_answers` property crashes with an AttributeError when the answers file contains non-dictionary YAML content (e.g., scalars, lists).

## Property-Based Test

```python
from hypothesis import given, strategies as st
from copier._subproject import Subproject
import tempfile
from pathlib import Path
import yaml

@given(
    yaml_content=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.none(),
        st.text(),
        st.lists(st.text())
    )
)
def test_subproject_handles_non_dict_yaml(yaml_content):
    """Test that Subproject handles non-dictionary YAML content gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        answers_file = tmpdir_path / ".copier-answers.yml"
        
        with answers_file.open("w") as f:
            yaml.dump(yaml_content, f)
        
        subproject = Subproject(local_abspath=tmpdir_path)
        # This should not crash
        last_answers = subproject.last_answers
        assert isinstance(last_answers, dict)
```

**Failing input**: `42` (or any non-dict value)

## Reproducing the Bug

```python
import tempfile
from pathlib import Path
from copier._subproject import Subproject

with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir_path = Path(tmpdir)
    answers_file = tmpdir_path / ".copier-answers.yml"
    
    with answers_file.open("w") as f:
        f.write("42")
    
    subproject = Subproject(local_abspath=tmpdir_path)
    print(subproject.last_answers)  # AttributeError: 'int' object has no attribute 'items'
```

## Why This Is A Bug

The `last_answers` property in `_subproject.py:64-69` assumes that `self._raw_answers` is always a dictionary and calls `.items()` on it without checking the type. However, YAML files can contain any type of data structure, not just dictionaries. When a user's answers file contains a scalar value, list, or null, the code crashes instead of handling it gracefully.

## Fix

```diff
--- a/copier/_subproject.py
+++ b/copier/_subproject.py
@@ -62,10 +62,13 @@ class Subproject:
 
     @cached_property
     def last_answers(self) -> AnyByStrDict:
         """Last answers, excluding private ones (except _src_path and _commit)."""
+        raw_answers = self._raw_answers
+        if not isinstance(raw_answers, dict):
+            return {}
         return {
             key: value
-            for key, value in self._raw_answers.items()
+            for key, value in raw_answers.items()
             if key in {"_src_path", "_commit"} or not key.startswith("_")
         }
```