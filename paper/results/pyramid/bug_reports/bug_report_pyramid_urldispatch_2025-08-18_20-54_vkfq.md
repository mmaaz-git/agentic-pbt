# Bug Report: pyramid.urldispatch Route Pattern Normalization Inconsistency

**Target**: `pyramid.urldispatch.Route`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The Route class stores the original un-normalized pattern in its `pattern` attribute, but internally uses a normalized version (with leading '/') for matching and generation, causing an inconsistency between what the pattern attribute reports and what the route actually matches.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pyramid.urldispatch as urldispatch
import string

@given(st.text(alphabet=string.ascii_letters + string.digits + '/{}-_:', min_size=1))
def test_route_pattern_normalization(pattern):
    route = urldispatch.Route('test', pattern)
    # The _compile_route function normalizes patterns to start with '/'
    # so the pattern attribute should reflect this normalization
    if route.match('/' + pattern) is not None:
        assert route.pattern.startswith('/'), f"Pattern {route.pattern} doesn't start with '/'"
```

**Failing input**: `'0'`

## Reproducing the Bug

```python
import pyramid.urldispatch as urldispatch

pattern = '0'
route = urldispatch.Route('test', pattern)

print(f"route.pattern = {route.pattern!r}")  # Output: '0'
print(f"route.match('0') = {route.match('0')}")  # Output: None
print(f"route.match('/0') = {route.match('/0')}")  # Output: {}
print(f"route.generate({}) = {route.generate({})!r}")  # Output: '/0'
```

## Why This Is A Bug

The Route class violates the principle of least surprise. The `pattern` attribute suggests the route matches '0', but it actually only matches '/0'. This inconsistency between the stored pattern and the actual matching behavior can confuse users and lead to incorrect assumptions about what paths a route will match.

## Fix

```diff
--- a/pyramid/urldispatch.py
+++ b/pyramid/urldispatch.py
@@ -14,8 +14,9 @@ class Route:
     def __init__(
         self, name, pattern, factory=None, predicates=(), pregenerator=None
     ):
-        self.pattern = pattern
-        self.path = pattern  # indefinite b/w compat, not in interface
+        # Normalize pattern to match what _compile_route expects
+        self.pattern = pattern if pattern.startswith('/') else '/' + pattern
+        self.path = self.pattern  # indefinite b/w compat, not in interface
         self.match, self.generate = _compile_route(pattern)
         self.name = name
         self.factory = factory
```