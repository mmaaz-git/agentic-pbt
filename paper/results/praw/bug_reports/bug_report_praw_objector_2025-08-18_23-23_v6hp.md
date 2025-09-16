# Bug Report: praw.objector TypeError on Lists with Primitives

**Target**: `praw.objector.Objector.objectify`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `objectify` method in PRAW's Objector class crashes with a TypeError when processing lists containing primitive types (integers, floats, etc.), which could occur in Reddit API responses.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import praw
from praw.objector import Objector

@given(st.lists(st.none() | st.booleans() | st.integers(), max_size=20))
def test_objectify_list_preserves_length(data):
    """objectify should preserve list length for simple data types."""
    reddit = praw.Reddit(
        client_id="test",
        client_secret="test",
        user_agent="test"
    )
    objector = Objector(reddit)
    result = objector.objectify(data)
    assert isinstance(result, list)
    assert len(result) == len(data)
```

**Failing input**: `[0]`

## Reproducing the Bug

```python
import praw
from praw.objector import Objector

reddit = praw.Reddit(
    client_id="test",
    client_secret="test",
    user_agent="test"
)

objector = Objector(reddit)

# Any list containing integers will fail
test_data = [0]
result = objector.objectify(test_data)  # TypeError: argument of type 'int' is not iterable
```

## Why This Is A Bug

The `objectify` method recursively processes list items (line 234), but after handling booleans, it assumes all remaining data is dict-like and attempts to check `"json" in data` (line 237) without verifying the type. This causes a TypeError when data is a primitive type like int, float, or str that doesn't support the `in` operator.

This violates expected behavior because:
1. Lists of IDs, scores, or timestamps are common in API responses
2. The method should handle all JSON-serializable types
3. The recursive call on lists naturally produces non-dict items

## Fix

```diff
--- a/praw/objector.py
+++ b/praw/objector.py
@@ -234,6 +234,9 @@ class Objector:
             return [self.objectify(item) for item in data]
         if isinstance(data, bool):  # Reddit.username_available
             return data
+        # Return non-dict primitives as-is
+        if not isinstance(data, dict):
+            return data
         if "json" in data and "errors" in data["json"]:
             errors = data["json"]["errors"]
             if len(errors) > 0:
```