# Bug Report: InquirerPy.containers.spinner Exception Handling Leaves Spinner in Inconsistent State

**Target**: `InquirerPy.containers.spinner.SpinnerWindow`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

SpinnerWindow's `_spinning` flag remains `True` when an exception occurs during the `start()` method, preventing the spinner from being restarted.

## Property-Based Test

```python
@pytest.mark.asyncio
async def test_spinner_exception_leaves_spinning_true():
    """
    If redraw() raises an exception during spinner execution,
    the _spinning flag remains True, preventing future start() calls.
    """
    loading_filter = Condition(lambda: True)
    redraw = Mock()
    redraw.side_effect = Exception("Redraw failed!")
    
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=["a", "b", "c"],
        delay=0.001
    )
    
    assert spinner._spinning == False
    
    with pytest.raises(Exception):
        await spinner.start()
    
    # BUG: _spinning remains True after exception
    assert spinner._spinning == True
```

**Failing input**: Any redraw callback that raises an exception

## Reproducing the Bug

```python
import asyncio
from InquirerPy.containers.spinner import SpinnerWindow
from prompt_toolkit.filters import Condition

async def main():
    loading_filter = Condition(lambda: True)
    
    def failing_redraw():
        raise RuntimeError("Redraw failed!")
    
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=failing_redraw,
        pattern=["a", "b", "c"],
        delay=0.001
    )
    
    print(f"Before: spinner._spinning = {spinner._spinning}")
    
    try:
        await spinner.start()
    except RuntimeError:
        pass
    
    print(f"After: spinner._spinning = {spinner._spinning}")
    # Output: After: spinner._spinning = True (should be False)

asyncio.run(main())
```

## Why This Is A Bug

The `_spinning` flag serves as a guard to prevent multiple concurrent spinner executions (lines 100-101 in spinner.py). When an exception occurs, the flag is never reset to `False` because the cleanup code at line 108 is never reached. This leaves the spinner in a permanently broken state where `start()` will always return immediately without doing anything, even after the error condition is resolved.

## Fix

```diff
--- a/InquirerPy/containers/spinner.py
+++ b/InquirerPy/containers/spinner.py
@@ -98,11 +98,14 @@ class SpinnerWindow(ConditionalContainer):
     async def start(self) -> None:
         """Start the spinner."""
         if self._spinning:
             return
         self._spinning = True
-        while self._loading():
-            for char in self._pattern:
-                await asyncio.sleep(self._delay)
-                self._char = char
-                self._redraw()
-        self._spinning = False
+        try:
+            while self._loading():
+                for char in self._pattern:
+                    await asyncio.sleep(self._delay)
+                    self._char = char
+                    self._redraw()
+        finally:
+            self._spinning = False
```