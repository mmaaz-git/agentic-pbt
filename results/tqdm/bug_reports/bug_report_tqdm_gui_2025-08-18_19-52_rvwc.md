# Bug Report: tqdm.gui Non-Idempotent close() Method

**Target**: `tqdm.gui.tqdm_gui.close`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `close()` method in `tqdm.gui.tqdm_gui` is not idempotent and raises `KeyError` when called multiple times, particularly when `__del__` is triggered after an explicit `close()`.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import tqdm.gui
from unittest.mock import patch

@given(params=st.fixed_dictionaries({
    'total': st.one_of(st.none(), st.integers(min_value=0, max_value=1000)),
    'disable': st.booleans()
}))
@settings(max_examples=100)
def test_close_idempotency(params):
    with patch('tqdm.gui.warn'):
        pbar = tqdm.gui.tqdm_gui(**params)
        
        # First close should work
        pbar.close()
        
        # Second close should also work (idempotent)
        pbar.close()  # This raises KeyError
        
        # __del__ after close should also be safe
        del pbar  # This also raises KeyError
```

**Failing input**: Any valid input triggers the bug when `close()` is called twice

## Reproducing the Bug

```python
import tqdm.gui
from unittest.mock import patch

with patch('tqdm.gui.warn'):
    # Create a progress bar
    pbar = tqdm.gui.tqdm_gui(total=100)
    
    # Close it once
    pbar.close()
    
    # Try to close again - raises KeyError
    try:
        pbar.close()
    except KeyError:
        print("BUG: close() raised KeyError on second call")
    
    # Or trigger __del__ after close - also raises KeyError
    del pbar  # Exception ignored in __del__
```

## Why This Is A Bug

The `close()` method should be idempotent (safe to call multiple times). The parent class `tqdm.std.tqdm` handles this correctly, but `tqdm.gui.tqdm_gui` directly calls `self._instances.remove(self)` without checking if the instance exists, causing `KeyError` when the instance has already been removed. This violates the principle of defensive programming and causes exceptions during garbage collection.

## Fix

```diff
--- a/tqdm/gui.py
+++ b/tqdm/gui.py
@@ -94,7 +94,10 @@ class tqdm_gui(std_tqdm):
         self.disable = True
 
         with self.get_lock():
-            self._instances.remove(self)
+            try:
+                self._instances.remove(self)
+            except KeyError:
+                pass  # Already removed
 
         # Restore toolbars
         self.mpl.rcParams['toolbar'] = self.toolbar
```