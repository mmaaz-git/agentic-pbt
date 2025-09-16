# Bug Report: flask.signals Integer 0 Cannot Be Used as Signal Sender

**Target**: `flask.signals` / `blinker.base.Signal`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The blinker Signal class crashes with AssertionError when attempting to connect a receiver to a sender with integer value 0, due to collision with the internal ANY_ID constant.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from blinker import Signal

@given(st.lists(st.integers(), min_size=1, max_size=5))
def test_any_sender_receives_all(senders):
    """Receivers connected to ANY should receive all sends."""
    signal = Signal()
    
    def receiver(sender, **kwargs):
        return "received"
    
    # This should work for any integer sender value
    signal.connect(receiver, sender=senders[0])
    signal.send(senders[0])
```

**Failing input**: `senders=[0]`

## Reproducing the Bug

```python
from blinker import Signal

signal = Signal()

def receiver(sender):
    return "received"

signal.connect(receiver, sender=0)  # Raises AssertionError
```

## Why This Is A Bug

The Signal class documentation states that any object can be used as a sender. The integer 0 is a valid Python object and should be usable as a sender identifier. However, the implementation uses `ANY_ID = 0` internally and `make_id(0)` returns 0, causing a collision. The assertion `assert sender_id != ANY_ID` in `_make_cleanup_sender` incorrectly rejects the legitimate sender value 0.

This violates the API contract that any hashable object can be used as a sender, and prevents users from using 0 as a sender value (e.g., for status codes, IDs, or simply the integer 0).

## Fix

```diff
--- a/blinker/base.py
+++ b/blinker/base.py
@@ -18,7 +18,7 @@ F = t.TypeVar("F", bound=c.Callable[..., t.Any])
 ANY = Symbol("ANY")
 """Symbol for "any sender"."""
 
-ANY_ID = 0
+ANY_ID = Symbol("ANY_ID")
 
 
 class Signal:
```

Alternative fix if Symbol cannot be used:

```diff
--- a/blinker/base.py
+++ b/blinker/base.py
@@ -18,7 +18,7 @@ F = t.TypeVar("F", bound=c.Callable[..., t.Any])
 ANY = Symbol("ANY")
 """Symbol for "any sender"."""
 
-ANY_ID = 0
+ANY_ID = object()  # Use a unique object instance
 
 
 class Signal:
```