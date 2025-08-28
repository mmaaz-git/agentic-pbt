# Bug Report: flask.views.MethodView Dynamic Method Detection Failure

**Target**: `flask.views.MethodView`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

MethodView fails to detect HTTP methods that are added dynamically after class definition, causing the `methods` attribute to remain None instead of being populated with the available HTTP methods.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from flask.views import MethodView, http_method_funcs

@given(methods=st.lists(st.sampled_from(list(http_method_funcs)), min_size=1, unique=True))
def test_methodview_dynamic_methods(methods):
    class TestView(MethodView):
        pass
    
    for method in methods:
        setattr(TestView, method, lambda self: "response")
    
    expected_methods = {m.upper() for m in methods}
    assert TestView.methods == expected_methods
```

**Failing input**: `methods=['get']` (or any HTTP method)

## Reproducing the Bug

```python
from flask.views import MethodView

def create_view_with_methods(methods):
    class DynamicView(MethodView):
        pass
    
    for method in methods:
        setattr(DynamicView, method, lambda self: f"{method} response")
    
    return DynamicView

ViewClass = create_view_with_methods(['get', 'post'])

print(f"ViewClass.methods: {ViewClass.methods}")  # None
print(f"Expected: {{'GET', 'POST'}}")  # Should be {'GET', 'POST'}

assert ViewClass.methods == {'GET', 'POST'}, f"Expected {{'GET', 'POST'}}, got {ViewClass.methods}"
```

## Why This Is A Bug

The MethodView.__init_subclass__ method is designed to automatically detect HTTP method handlers and populate the `methods` attribute. This feature is documented and expected to work, but it only functions when methods are defined in the class body at class definition time. When methods are added dynamically after class creation (a common pattern in factory functions, decorators, or testing), the `methods` attribute is not updated, breaking the automatic method detection feature.

This violates the expected behavior because:
1. The class has valid HTTP method handlers attached to it
2. The Flask routing system relies on the `methods` attribute to determine allowed HTTP methods
3. Users expect the automatic detection to work regardless of when methods are added

## Fix

The issue occurs because `__init_subclass__` is only called once when the class is defined. A potential fix would be to compute methods lazily or provide a method to refresh the methods attribute:

```diff
class MethodView(View):
    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        super().__init_subclass__(**kwargs)

        if "methods" not in cls.__dict__:
+           cls._compute_methods()
+
+   @classmethod
+   def _compute_methods(cls) -> None:
            methods = set()

            for base in cls.__bases__:
                if getattr(base, "methods", None):
                    methods.update(base.methods)

            for key in http_method_funcs:
                if hasattr(cls, key):
                    methods.add(key.upper())

            if methods:
                cls.methods = methods
```

Or alternatively, make `methods` a property that computes the value dynamically when accessed.