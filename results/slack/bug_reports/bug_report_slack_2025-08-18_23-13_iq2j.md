# Bug Report: slack Module Incompatible with Python 3.11+

**Target**: `slack` module (dependency injection container)
**Severity**: High
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The slack module uses the deprecated `inspect.getargspec()` function which was removed in Python 3.11, causing AttributeError on all operations that invoke functions.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import slack

@given(st.text(min_size=1), st.integers())
def test_container_registration_and_retrieval(name, value):
    container = slack.Container()
    container.register(name, value)
    assert container.provide(name) == value
```

**Failing input**: Any input triggers the bug (e.g., `name="test", value=42`)

## Reproducing the Bug

```python
import sys
sys.path.append('/root/hypothesis-llm/envs/slack_env/lib/python3.13/site-packages')
import slack

container = slack.Container()
container.register("test", 42)
result = container.provide("test")
```

## Why This Is A Bug

The `inspect.getargspec()` function was deprecated in Python 3.0 and removed in Python 3.11. The slack module uses this function in its `invoke()` method (line 68), making it incompatible with Python 3.11+. This breaks all core functionality of the module since `invoke()` is called whenever components are provided or functions are applied.

## Fix

```diff
--- a/slack/__init__.py
+++ b/slack/__init__.py
@@ -65,7 +65,7 @@ class ParamterMissingError(Exception):
 
 def invoke(fn, *param_dicts):
     "call a function with a list of dicts providing params"
-    spec = inspect.getargspec(fn)
+    spec = inspect.getfullargspec(fn)
     if not spec.args:
         return fn()
```