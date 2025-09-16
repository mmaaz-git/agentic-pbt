# Bug Report: tqdm.notebook AttributeError in close() after failed initialization

**Target**: `tqdm.notebook.tqdm_notebook`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

When `tqdm_notebook` initialization fails due to missing ipywidgets, the object is left in an inconsistent state where the `disp` attribute is not set, causing an AttributeError when `close()` is called during garbage collection.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from tqdm.notebook import tqdm_notebook

@given(st.booleans(), st.booleans())
def test_initialization_consistency(gui, disable):
    """Test that tqdm_notebook always sets disp attribute or fails completely"""
    try:
        t = tqdm_notebook(range(10), gui=gui, disable=disable)
        # If initialization succeeds, disp must be set
        assert hasattr(t, 'disp'), "Successfully initialized tqdm must have disp attribute"
        t.close()
    except ImportError:
        # If initialization fails, the object should not be partially constructed
        pass
```

**Failing input**: `gui=False, disable=False` (when ipywidgets is not available)

## Reproducing the Bug

```python
from tqdm.notebook import tqdm_notebook

try:
    t = tqdm_notebook(range(10), gui=False, disable=False)
    t.close()
except ImportError as e:
    print(f"ImportError: {e}")
    # Object is garbage collected here, triggering the AttributeError
```

## Why This Is A Bug

The `__init__` method can fail partway through initialization when ipywidgets is not available. It raises an ImportError at line 234 before setting the `disp` attribute at line 240. When the partially-constructed object is garbage collected, `__del__` calls `close()`, which tries to call `self.disp` at line 279, causing an AttributeError. The object should either be fully initialized or not created at all.

## Fix

The `disp` attribute should be set before any operation that might raise an exception, or `close()` should check if `disp` exists before calling it.

```diff
--- a/tqdm/notebook.py
+++ b/tqdm/notebook.py
@@ -221,8 +221,10 @@ class tqdm_notebook(std_tqdm):
         colour = kwargs.pop('colour', None)
         display_here = kwargs.pop('display', True)
         super().__init__(*args, **kwargs)
+        # Set default disp early to avoid AttributeError in close()
+        self.disp = lambda *_, **__: None
         if self.disable or not kwargs['gui']:
-            self.disp = lambda *_, **__: None
             return
 
         # Get bar width
@@ -276,7 +278,7 @@ class tqdm_notebook(std_tqdm):
         # Try to detect if there was an error or KeyboardInterrupt
         # in manual mode: if n < total, things probably got wrong
         if self.total and self.n < self.total:
-            self.disp(bar_style='danger', check_delay=False)
+            if hasattr(self, 'disp'):
+                self.disp(bar_style='danger', check_delay=False)
         else:
             if self.leave:
-                self.disp(bar_style='success', check_delay=False)
+                if hasattr(self, 'disp'):
+                    self.disp(bar_style='success', check_delay=False)
             else:
-                self.disp(close=True, check_delay=False)
+                if hasattr(self, 'disp'):
+                    self.disp(close=True, check_delay=False)
```