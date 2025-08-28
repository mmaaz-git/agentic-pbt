# Bug Report: troposphere.utils Type Error in get_events Function

**Target**: `troposphere.utils.get_events`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `get_events` function fails to properly flatten event batches because it appends response objects directly instead of converting them to lists first, causing `sum()` to fail with non-list iterables.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from unittest.mock import MagicMock
import troposphere.utils as utils

class MockEvent:
    def __init__(self, event_id):
        self.event_id = event_id

@given(st.lists(st.lists(st.integers(min_value=0, max_value=1000), min_size=0, max_size=10), min_size=0, max_size=10))
def test_get_events_list_operations(event_batches):
    mock_batches = []
    for batch in event_batches:
        mock_batch = [MockEvent(event_id=f"event-{i}") for i in batch]
        mock_batches.append(mock_batch)
    
    mock_conn = MagicMock()
    batch_iter = iter(mock_batches)
    
    def describe_side_effect(stackname, next_token):
        try:
            batch = next(batch_iter)
            result = MagicMock()
            result.__iter__ = lambda self: iter(batch)
            result.next_token = None if batch == mock_batches[-1] else "token"
            return result
        except StopIteration:
            result = MagicMock()
            result.__iter__ = lambda self: iter([])
            result.next_token = None
            return result
    
    mock_conn.describe_stack_events.side_effect = describe_side_effect
    
    if mock_batches:
        result = list(utils.get_events(mock_conn, "test-stack"))
        expected = []
        for batch in mock_batches:
            expected.extend(batch)
        expected = list(reversed(expected))
        assert len(result) == len(expected)
```

**Failing input**: `event_batches=[[0]]`

## Reproducing the Bug

```python
from unittest.mock import MagicMock
import troposphere.utils as utils

class MockEvent:
    def __init__(self, event_id):
        self.event_id = event_id

mock_conn = MagicMock()
event = MockEvent("event-1")

mock_response = MagicMock()
mock_response.__iter__ = lambda self: iter([event])
mock_response.next_token = None

mock_conn.describe_stack_events.return_value = mock_response

result = list(utils.get_events(mock_conn, "test-stack"))
print(f"Expected: 1 event, Got: {len(result)} events")
assert len(result) == 1, "Bug: get_events returns empty list for single batch"
```

## Why This Is A Bug

The `get_events` function at line 14 does `event_list.append(events)` where `events` is an iterable response object, not a list. When `sum(event_list, [])` at line 19 tries to flatten these objects, it fails because `sum()` expects lists to concatenate with the initial empty list `[]`. This causes the function to return incorrect results or fail entirely when working with AWS SDK response objects that are iterable but not lists.

## Fix

```diff
--- a/troposphere/utils.py
+++ b/troposphere/utils.py
@@ -11,7 +11,7 @@ def get_events(conn, stackname):
     event_list = []
     while 1:
         events = conn.describe_stack_events(stackname, next)
-        event_list.append(events)
+        event_list.append(list(events))
         if events.next_token is None:
             break
         next = events.next_token
```