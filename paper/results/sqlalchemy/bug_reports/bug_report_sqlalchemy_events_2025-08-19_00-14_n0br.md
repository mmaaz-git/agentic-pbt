# Bug Report: sqlalchemy.events Undocumented Listener Deduplication

**Target**: `sqlalchemy.event.listen`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

SQLAlchemy's event system silently deduplicates identical listener functions when registered multiple times, but this behavior is undocumented and violates reasonable API expectations.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine, event
from sqlalchemy.pool import NullPool

@given(st.integers(min_value=1, max_value=10))
@settings(max_examples=50)
def test_event_multiple_registrations(num_registrations):
    """Test that registering the same listener multiple times results in multiple calls"""
    engine = create_engine('sqlite:///:memory:', poolclass=NullPool)
    
    counter = {'count': 0}
    
    def connect_listener(dbapi_conn, connection_record):
        counter['count'] += 1
    
    # Register the same listener multiple times
    for _ in range(num_registrations):
        event.listen(engine.pool, 'connect', connect_listener)
    
    # Trigger the event once
    conn = engine.connect()
    conn.close()
    
    # The listener should have been called num_registrations times
    assert counter['count'] == num_registrations
```

**Failing input**: `num_registrations=2`

## Reproducing the Bug

```python
from sqlalchemy import create_engine, event
from sqlalchemy.pool import NullPool

engine = create_engine('sqlite:///:memory:', poolclass=NullPool)

counter = {'count': 0}

def connect_listener(dbapi_conn, connection_record):
    counter['count'] += 1

# Register the same listener twice
event.listen(engine.pool, 'connect', connect_listener)
event.listen(engine.pool, 'connect', connect_listener)

# Trigger the event once
conn = engine.connect()
conn.close()

print(f"Expected calls: 2")
print(f"Actual calls: {counter['count']}")
assert counter['count'] == 2, f"Expected 2 calls, got {counter['count']}"
```

## Why This Is A Bug

The `event.listen()` function accepts duplicate registrations without error or warning, and `event.contains()` returns `True` after each registration, suggesting the listener is registered multiple times. However, the listener is only called once per event trigger, not once per registration. This violates the principle of least surprise and contradicts what the API appears to promise. The documentation does not mention that duplicate registrations are deduplicated.

## Fix

The issue can be addressed in one of two ways:

1. **Document the deduplication behavior** - Add clear documentation that identical listener functions are automatically deduplicated

2. **Change the implementation** - Allow multiple registrations of the same function to result in multiple calls

```diff
# Option 1: Documentation fix in event.listen() docstring
def listen(target, identifier, fn, *args, **kw):
    """Register a listener function for the given target.
    
+   Note: If the same function object is registered multiple times
+   for the same event, it will only be called once per event trigger.
+   SQLAlchemy automatically deduplicates identical listener registrations.
    
    The :func:`.listen` function is part of the primary interface for the
    SQLAlchemy event system, documented at :ref:`event_toplevel`.
```