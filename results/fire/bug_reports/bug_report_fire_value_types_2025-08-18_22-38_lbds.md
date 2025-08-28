# Bug Report: fire.value_types Documentation Contract Violation in HasCustomStr

**Target**: `fire.value_types.HasCustomStr`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `HasCustomStr` function's docstring claims that primitives like ints and floats have custom `__str__` methods, but the implementation returns `False` for these types.

## Property-Based Test

```python
def test_has_custom_str_on_primitives():
    """Primitives should have custom __str__ according to docstring."""
    assert vt.HasCustomStr(42), "int should have custom __str__"
    assert vt.HasCustomStr(3.14), "float should have custom __str__"
    assert vt.HasCustomStr(True), "bool should have custom __str__"
```

**Failing input**: `42` (and any int, float, bool, or complex value)

## Reproducing the Bug

```python
import fire.value_types as vt

result = vt.HasCustomStr(42)
print(f"HasCustomStr(42) = {result}")

result = vt.HasCustomStr(3.14)  
print(f"HasCustomStr(3.14) = {result}")
```

## Why This Is A Bug

The docstring explicitly states: "This means that the __str__ methods of primitives like ints and floats are considered custom." However, the implementation checks if `__str__` is defined by the class itself (not by `object`). For int, float, bool, and complex types, `__str__` is inherited from `object`, causing `HasCustomStr` to return `False`.

This creates a contract violation where the documented behavior contradicts the actual behavior. While this doesn't affect the overall module functionality (primitives are still classified as values via `VALUE_TYPES`), developers relying on `HasCustomStr`'s documented behavior would get unexpected results.

## Fix

Either update the docstring to reflect actual behavior or modify the implementation to match the documentation. Here's the docstring fix:

```diff
 def HasCustomStr(component):
   """Determines if a component has a custom __str__ method.
 
   Uses inspect.classify_class_attrs to determine the origin of the object's
   __str__ method, if one is present. If it defined by `object` itself, then
-  it is not considered custom. Otherwise it is. This means that the __str__
-  methods of primitives like ints and floats are considered custom.
+  it is not considered custom. Otherwise it is. Note that built-in types
+  like int, float, bool, and complex inherit __str__ from object and are
+  therefore not considered to have custom __str__ methods. Types like str
+  and bytes do have their own __str__ implementations and are considered custom.
 
   Objects with custom __str__ methods are treated as values and can be
   serialized in places where more complex objects would have their help screen
   shown instead.
```