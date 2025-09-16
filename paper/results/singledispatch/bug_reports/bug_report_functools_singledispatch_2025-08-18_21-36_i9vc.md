# Bug Report: functools.singledispatch Class Decorator Corruption

**Target**: `functools.singledispatch`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Using `@func.register` decorator on a class without specifying a type argument silently corrupts the class definition, replacing it with a lambda function and breaking expected behavior.

## Property-Based Test

```python
def test_class_decorator_syntax():
    @functools.singledispatch
    def process(obj):
        return "default"
    
    @process.register
    class Handler:
        def __init__(self, value):
            self.value = value
    
    instance = Handler(42)
    
    # Expected: instance should be a Handler object
    # Actual: instance is the integer 42
    assert isinstance(instance, Handler)  # FAILS
```

**Failing input**: Using `@process.register` decorator on a class without type argument

## Reproducing the Bug

```python
import functools

@functools.singledispatch
def process(obj):
    return "default"

@process.register
class Handler:
    def __init__(self, value: int):
        self.value = value

# Handler is now a function, not a class
print(type(Handler))  # <class 'function'>

# Calling Handler(42) returns 42, not a Handler instance
result = Handler(42)
print(result)  # 42
print(type(result))  # <class 'int'>

# The original Handler class is lost
# Cannot create Handler instances anymore
```

## Why This Is A Bug

The decorator silently corrupts the class definition instead of either:
1. Properly registering the class as a dispatchable type
2. Raising an error for invalid usage

This violates the principle of least surprise and can lead to confusing runtime errors when the "class" is used later in the code.

## Fix

The `register` method should detect when it's being used as a bare decorator on a class and either:
1. Raise a clear error message explaining proper usage
2. Handle the class registration correctly by using the class itself as the dispatch type

Here's a potential fix approach:

```diff
# In functools.py, within the register function:
def register(cls, func=None):
    if func is None:
        if isinstance(cls, type):
            # cls is a class being decorated without explicit type
+           raise TypeError(
+               f"Cannot use @{funcname}.register on a class without "
+               f"specifying the type to register for. "
+               f"Use @{funcname}.register(SomeType) instead."
+           )
        # existing annotation-based registration logic
        ...
```

Alternatively, make it work as users might expect by registering the class for its own type:

```diff
def register(cls, func=None):
    if func is None:
        if isinstance(cls, type):
+           # Register the class to handle instances of itself
+           registry[cls] = cls
+           return cls
        # existing logic
        ...
```