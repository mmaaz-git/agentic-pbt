# Bug Report: sqlalchemy.event RuntimeError on Listener Modification During Execution

**Target**: `sqlalchemy.event`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

Modifying event listeners (adding or removing) during event execution causes an unhandled `RuntimeError: deque mutated during iteration` instead of a graceful error or deferred modification.

## Property-Based Test

```python
from sqlalchemy import create_engine, event

def test_listener_modification_during_execution():
    """Test that modifying listeners during execution is handled gracefully."""
    engine = create_engine('sqlite:///:memory:')
    
    def self_removing_listener(dbapi_conn, connection_record):
        event.remove(engine, 'connect', self_removing_listener)
    
    event.listen(engine, 'connect', self_removing_listener)
    
    # This raises RuntimeError: deque mutated during iteration
    with engine.connect() as conn:
        pass
```

**Failing input**: Any attempt to modify listeners during event execution

## Reproducing the Bug

```python
from sqlalchemy import create_engine, event

engine = create_engine('sqlite:///:memory:')

def self_removing_listener(dbapi_conn, connection_record):
    event.remove(engine, 'connect', self_removing_listener)

event.listen(engine, 'connect', self_removing_listener)

with engine.connect() as conn:
    pass
```

## Why This Is A Bug

While the SQLAlchemy documentation mentions that "The :func:`.remove` function cannot be called at the same time that the target event is being run", the actual behavior is a low-level `RuntimeError` that crashes the application. A well-designed API should either:
1. Queue modifications for after event execution completes
2. Raise a descriptive exception like `EventModificationDuringExecutionError`
3. Silently ignore the modification attempt with a warning

The current behavior exposes internal implementation details through the error message "deque mutated during iteration".

## Fix

The issue occurs in `/root/.local/lib/python3.13/site-packages/sqlalchemy/event/attr.py` at line 496. A defensive fix would be to create a copy of the listeners before iteration:

```diff
--- a/sqlalchemy/event/attr.py
+++ b/sqlalchemy/event/attr.py
@@ -493,7 +493,7 @@ class _JoinedListener(_ListenerCollection):
     def __call__(self, *args, **kw):
-        for fn in self.listeners:
+        for fn in list(self.listeners):
             fn(*args, **kw)
```

Alternatively, a more robust solution would detect modification attempts and raise a descriptive error:

```diff
--- a/sqlalchemy/event/attr.py
+++ b/sqlalchemy/event/attr.py
@@ -493,7 +493,12 @@ class _JoinedListener(_ListenerCollection):
     def __call__(self, *args, **kw):
+        self._iterating = True
+        try:
             for fn in self.listeners:
                 fn(*args, **kw)
+        finally:
+            self._iterating = False
+
+    # In listen/remove methods, check self._iterating and raise descriptive error
```