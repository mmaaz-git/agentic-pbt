# Bug Report: tqdm.asyncio.gather Improper Exception Handling

**Target**: `tqdm.asyncio.tqdm_asyncio.gather`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

`tqdm_asyncio.gather()` fails to properly handle exceptions from multiple tasks, leaving unhandled task exceptions that trigger "Task exception was never retrieved" warnings.

## Property-Based Test

```python
@given(st.lists(st.integers(), min_size=2, max_size=10))
@settings(max_examples=50, deadline=5000)
def test_gather_with_exceptions(values):
    """Test gather behavior when some tasks fail."""
    
    async def create_task(value):
        if value < 0:
            raise ValueError(f"Negative value: {value}")
        await asyncio.sleep(0.001)
        return value
    
    async def run_test():
        mixed_values = values[:len(values)//2] + [-1] + values[len(values)//2:]
        tasks = [create_task(val) for val in mixed_values]
        
        try:
            results = await tqdm_asyncio.gather(*tasks, total=len(tasks), leave=False)
            assert all(v >= 0 for v in mixed_values), "Should have raised ValueError for negative values"
        except ValueError:
            assert any(v < 0 for v in mixed_values), "ValueError raised but no negative values"
    
    asyncio.run(run_test())
```

**Failing input**: `[0, 1, -1, 2]` (any list with multiple negative values triggers the issue)

## Reproducing the Bug

```python
import asyncio
from tqdm.asyncio import tqdm_asyncio

async def reproduce_bug():
    async def task_that_fails(n):
        await asyncio.sleep(0.01 * n)
        raise ValueError(f"Failed task {n}")
    
    tasks = [task_that_fails(i) for i in range(3)]
    
    try:
        await tqdm_asyncio.gather(*tasks, leave=False)
    except ValueError as e:
        print(f"Caught: {e}")
    
    await asyncio.sleep(0.1)

asyncio.run(reproduce_bug())
```

## Why This Is A Bug

The `gather()` method should handle all task exceptions properly, similar to `asyncio.gather()`. Instead, it only catches the first exception and leaves other failed tasks unhandled, causing Python to emit "Task exception was never retrieved" warnings. This violates the expected behavior where all tasks should be properly awaited and their exceptions handled.

## Fix

```diff
--- a/tqdm/asyncio.py
+++ b/tqdm/asyncio.py
@@ -75,8 +75,18 @@ class tqdm_asyncio(std_tqdm):
         async def wrap_awaitable(i, f):
             return i, await f
 
         ifs = [wrap_awaitable(i, f) for i, f in enumerate(fs)]
-        res = [await f for f in cls.as_completed(ifs, loop=loop, timeout=timeout,
-                                                 total=total, **tqdm_kwargs)]
+        res = []
+        first_exception = None
+        async for f in cls.as_completed(ifs, loop=loop, timeout=timeout,
+                                       total=total, **tqdm_kwargs):
+            try:
+                res.append(await f)
+            except Exception as e:
+                if first_exception is None:
+                    first_exception = e
+                # Continue to await remaining tasks
+        
+        if first_exception:
+            raise first_exception
         return [i for _, i in sorted(res)]
```