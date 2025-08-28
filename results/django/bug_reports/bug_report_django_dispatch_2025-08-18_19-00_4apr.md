# Bug Report: django.dispatch.Signal TypeError with Caching and Non-Weakrefable Senders

**Target**: `django.dispatch.Signal`
**Severity**: High
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

Signal with `use_caching=True` crashes with TypeError when sending signals with non-weakrefable senders like plain `object()` instances, integers, strings, lists, or dictionaries.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from django.dispatch import Signal

@given(use_caching=st.booleans(), num_senders=st.integers(min_value=1, max_value=5))
def test_caching_consistency(use_caching, num_senders):
    signal = Signal(use_caching=use_caching)
    senders = [object() for _ in range(num_senders)]
    
    def receiver(sender, **kwargs):
        return "response"
    
    for sender in senders:
        signal.connect(receiver, sender=sender, weak=False)
    
    for sender in senders:
        responses = signal.send(sender=sender)
        assert len(responses) == 1
```

**Failing input**: `use_caching=True, num_senders=1`

## Reproducing the Bug

```python
from django.dispatch import Signal

signal = Signal(use_caching=True)

def receiver(sender, **kwargs):
    return "response"

signal.connect(receiver, weak=False)

sender = object()
responses = signal.send(sender=sender)
```

## Why This Is A Bug

The Signal class uses `weakref.WeakKeyDictionary` for `sender_receivers_cache` when caching is enabled. However, many common Python objects cannot be weakly referenced, including:
- Plain `object()` instances  
- Built-in types (int, str, list, dict, tuple, etc.)

This causes a TypeError when the cache tries to store these senders as weak keys, making the caching feature unusable with common sender types.

## Fix

```diff
--- a/django/dispatch/dispatcher.py
+++ b/django/dispatch/dispatcher.py
@@ -178,11 +178,16 @@ class Signal:
 
         Return a list of tuple pairs [(receiver, response), ... ].
         """
+        # Check cache if caching is enabled
         if (
             not self.receivers
             or self.sender_receivers_cache.get(sender) is NO_RECEIVERS
         ):
             return []
+        
+        # Handle WeakKeyDictionary limitation for non-weakrefable objects
+        if self.use_caching and sender is not None:
+            try:
+                weakref.ref(sender)
+            except TypeError:
+                # Skip caching for non-weakrefable senders
+                pass
+            else:
+                cached = self.sender_receivers_cache.get(sender)
+                if cached is NO_RECEIVERS:
+                    return []
+        
         responses = []
         sync_receivers, async_receivers = self._live_receivers(sender)
```

Alternative fix: Use a regular dict with manual cleanup or handle the TypeError gracefully in cache operations.