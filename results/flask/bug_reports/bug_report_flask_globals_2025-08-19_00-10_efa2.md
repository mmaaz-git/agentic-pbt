# Bug Report: flask.globals Context Push/Pop State Sharing

**Target**: `flask.globals` / `flask.ctx.AppContext`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

Multiple pushes of the same Flask AppContext share the same `g` object instead of creating isolated namespaces, causing unexpected state leakage between what should be isolated context levels.

## Property-Based Test

```python
@given(st.integers(min_value=0, max_value=10))
def test_repeated_push_pop_context(num_pushes):
    """Test that repeated push/pop of contexts works correctly."""
    app = flask.Flask(__name__)
    
    with app.app_context() as ctx:
        # Set initial value
        g.base_value = "base"
        
        # Push multiple times
        for i in range(num_pushes):
            ctx.push()
            # Each push should maintain the value
            assert g.base_value == "base"
            g.base_value = f"level_{i}"
        
        # Pop multiple times
        for i in range(num_pushes):
            ctx.pop()
        
        # Should still have access to g in the original context
        assert hasattr(g, 'base_value')
```

**Failing input**: `num_pushes=2`

## Reproducing the Bug

```python
import flask
from flask import g

app = flask.Flask(__name__)

with app.app_context() as ctx:
    g.data = "initial"
    print(f"1. Set g.data = 'initial'")
    
    ctx.push()
    print(f"2. After ctx.push(), g.data = '{g.data}'")
    
    g.data = "modified"
    print(f"3. Modified g.data = 'modified'")
    
    ctx.push()
    print(f"4. After another ctx.push(), g.data = '{g.data}'")
    
    ctx.pop()
    print(f"5. After ctx.pop(), g.data = '{g.data}'")
    
    ctx.pop()
    print(f"6. After another ctx.pop(), g.data = '{g.data}'")
```

Output:
```
1. Set g.data = 'initial'
2. After ctx.push(), g.data = 'initial'
3. Modified g.data = 'modified'
4. After another ctx.push(), g.data = 'modified'
5. After ctx.pop(), g.data = 'modified'
6. After another ctx.pop(), g.data = 'modified'
```

## Why This Is A Bug

When pushing an AppContext multiple times, each push should ideally provide an isolated namespace for `g` to prevent state leakage between context levels. Currently, all pushes of the same context share the same `g` object, which means modifications at any nesting level affect all other levels. This violates the principle of isolation that contexts are meant to provide and could lead to subtle bugs in applications that use nested contexts or recursive functions with contexts.

## Fix

The issue stems from the fact that `AppContext.__init__` creates a single `g` object that is reused for all pushes of that context. A potential fix would be to maintain a stack of `g` objects corresponding to the push depth:

```diff
 class AppContext:
     def __init__(self, app: Flask) -> None:
         self.app = app
         self.url_adapter = app.create_url_adapter(None)
-        self.g: _AppCtxGlobals = app.app_ctx_globals_class()
+        self._g_stack: list[_AppCtxGlobals] = [app.app_ctx_globals_class()]
         self._cv_tokens: list[contextvars.Token[AppContext]] = []
+    
+    @property
+    def g(self) -> _AppCtxGlobals:
+        return self._g_stack[-1]
     
     def push(self) -> None:
         """Binds the app context to the current context."""
+        if self._cv_tokens:  # If already pushed, create new g
+            self._g_stack.append(self.app.app_ctx_globals_class())
         self._cv_tokens.append(_cv_app.set(self))
         appcontext_pushed.send(self.app, _async_wrapper=self.app.ensure_sync)
     
     def pop(self, exc: BaseException | None = _sentinel) -> None:
         """Pops the app context."""
         try:
             if len(self._cv_tokens) == 1:
                 if exc is _sentinel:
                     exc = sys.exc_info()[1]
                 self.app.do_teardown_appcontext(exc)
+            elif len(self._g_stack) > 1:
+                self._g_stack.pop()
         finally:
             ctx = _cv_app.get()
             _cv_app.reset(self._cv_tokens.pop())
```