# Bug Report: django.dispatch.Signal dispatch_uid Requires Matching Sender

**Target**: `django.dispatch.Signal.disconnect`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `dispatch_uid` parameter doesn't work as documented - it requires the sender to match even when a unique dispatch_uid is provided, defeating the purpose of dispatch_uid as a unique identifier.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from django.dispatch import Signal

@given(
    connect_with_sender=st.booleans(),
    disconnect_with_sender=st.booleans()
)
def test_dispatch_uid_sender_independence(connect_with_sender, disconnect_with_sender):
    signal = Signal()
    
    def receiver(sender, **kwargs):
        return "response"
    
    connect_sender = object() if connect_with_sender else None
    disconnect_sender = object() if disconnect_with_sender else None
    
    signal.connect(receiver, sender=connect_sender, dispatch_uid="unique_id")
    
    # Should be able to disconnect with just dispatch_uid
    result = signal.disconnect(sender=disconnect_sender, dispatch_uid="unique_id")
    
    # dispatch_uid should be sufficient to identify the connection
    assert result is True
```

**Failing input**: `connect_with_sender=False, disconnect_with_sender=True`

## Reproducing the Bug

```python
from django.dispatch import Signal

signal = Signal()

def receiver(sender, **kwargs):
    return "response"

signal.connect(receiver, sender=None, dispatch_uid="my_uid")

result = signal.disconnect(sender=object(), dispatch_uid="my_uid")
print(f"Disconnect returned: {result}")

result2 = signal.disconnect(sender=None, dispatch_uid="my_uid")
print(f"Disconnect with matching sender returned: {result2}")
```

## Why This Is A Bug

The documentation states that `dispatch_uid` is "An identifier used to uniquely identify a particular instance of a receiver." However, the implementation includes the sender in the lookup_key even when dispatch_uid is provided:

```python
if dispatch_uid:
    lookup_key = (dispatch_uid, _make_id(sender))
```

This means you cannot disconnect a receiver by dispatch_uid alone - you must also know and provide the exact sender that was used during connect(), which defeats the purpose of having a unique identifier.

## Fix

```diff
--- a/django/dispatch/dispatcher.py
+++ b/django/dispatch/dispatcher.py
@@ -95,7 +95,7 @@ class Signal:
 
         if dispatch_uid:
-            lookup_key = (dispatch_uid, _make_id(sender))
+            lookup_key = (dispatch_uid, None)
         else:
             lookup_key = (_make_id(receiver), _make_id(sender))
 
@@ -137,7 +137,7 @@ class Signal:
         """
         if dispatch_uid:
-            lookup_key = (dispatch_uid, _make_id(sender))
+            lookup_key = (dispatch_uid, None)
         else:
             lookup_key = (_make_id(receiver), _make_id(sender))
```

This change makes dispatch_uid truly unique across all senders, allowing disconnection by dispatch_uid alone as intended.