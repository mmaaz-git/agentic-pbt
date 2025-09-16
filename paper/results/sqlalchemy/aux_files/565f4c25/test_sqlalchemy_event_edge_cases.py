import string
import uuid
import weakref
from typing import Callable

import pytest
from hypothesis import assume, given, settings, strategies as st
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine
from sqlalchemy import event


def make_unique_function():
    """Create a unique function for testing."""
    unique_id = str(uuid.uuid4())
    
    def listener(*args, **kwargs):
        pass
    
    listener.__name__ = f'listener_{unique_id}'
    listener._unique_id = unique_id
    return listener


def test_weakref_function():
    """Test behavior with weakref to functions."""
    target = create_engine('sqlite:///:memory:')
    identifier = 'connect'
    
    def my_listener(*args, **kwargs):
        pass
    
    # Create a weakref to the function
    weak_fn = weakref.ref(my_listener)
    
    # Try to register the weakref itself (not the function it points to)
    try:
        event.listen(target, identifier, weak_fn)
        # If it succeeds, check if it's registered
        if event.contains(target, identifier, weak_fn):
            event.remove(target, identifier, weak_fn)
    except (TypeError, AttributeError) as e:
        # Expected - weakref is not directly callable
        pass
    
    # Now try with the dereferenced function
    fn = weak_fn()
    if fn is not None:
        event.listen(target, identifier, fn)
        assert event.contains(target, identifier, fn)
        event.remove(target, identifier, fn)


def test_callable_object():
    """Test with custom callable objects."""
    target = create_engine('sqlite:///:memory:')
    identifier = 'connect'
    
    class CallableClass:
        def __init__(self, value):
            self.value = value
            self.call_count = 0
        
        def __call__(self, *args, **kwargs):
            self.call_count += 1
            return self.value
    
    callable_obj = CallableClass(42)
    
    # Register the callable object
    event.listen(target, identifier, callable_obj)
    assert event.contains(target, identifier, callable_obj)
    
    # Create another instance with same value
    callable_obj2 = CallableClass(42)
    
    # This should NOT be registered (different object)
    assert not event.contains(target, identifier, callable_obj2)
    
    # Register the second one
    event.listen(target, identifier, callable_obj2)
    assert event.contains(target, identifier, callable_obj2)
    
    # Remove first one - second should remain
    event.remove(target, identifier, callable_obj)
    assert not event.contains(target, identifier, callable_obj)
    assert event.contains(target, identifier, callable_obj2)
    
    # Clean up
    event.remove(target, identifier, callable_obj2)


def test_function_with_same_id():
    """Test what happens when functions have the same id/name but are different objects."""
    target = create_engine('sqlite:///:memory:')
    identifier = 'connect'
    
    # Create two functions with the same name
    def make_function_with_name(name):
        def listener(*args, **kwargs):
            pass
        listener.__name__ = name
        return listener
    
    fn1 = make_function_with_name('same_name')
    fn2 = make_function_with_name('same_name')
    
    # They should be different objects
    assert fn1 is not fn2
    assert fn1.__name__ == fn2.__name__
    
    # Register first
    event.listen(target, identifier, fn1)
    assert event.contains(target, identifier, fn1)
    
    # Second should not be registered yet
    assert not event.contains(target, identifier, fn2)
    
    # Register second
    event.listen(target, identifier, fn2)
    assert event.contains(target, identifier, fn2)
    assert event.contains(target, identifier, fn1)  # First should still be there
    
    # Remove first
    event.remove(target, identifier, fn1)
    assert not event.contains(target, identifier, fn1)
    assert event.contains(target, identifier, fn2)  # Second should remain
    
    # Clean up
    event.remove(target, identifier, fn2)


def test_builtin_functions():
    """Test with built-in functions."""
    target = create_engine('sqlite:///:memory:')
    identifier = 'connect'
    
    # Try with built-in functions
    builtins = [print, len, str, int]
    
    for builtin_fn in builtins:
        try:
            event.listen(target, identifier, builtin_fn)
            assert event.contains(target, identifier, builtin_fn)
            event.remove(target, identifier, builtin_fn)
            assert not event.contains(target, identifier, builtin_fn)
        except Exception as e:
            # Some built-ins might not work as event listeners
            print(f"Built-in {builtin_fn.__name__} failed: {e}")


def test_partial_functions():
    """Test with functools.partial."""
    from functools import partial
    
    target = create_engine('sqlite:///:memory:')
    identifier = 'connect'
    
    def base_function(x, y, *args, **kwargs):
        return x + y
    
    # Create partial functions
    partial1 = partial(base_function, 1)
    partial2 = partial(base_function, 2)
    partial3 = partial(base_function, 1)  # Same as partial1 but different object
    
    # Register first partial
    event.listen(target, identifier, partial1)
    assert event.contains(target, identifier, partial1)
    
    # Second partial should not be registered
    assert not event.contains(target, identifier, partial2)
    
    # Third partial (same args as first) should also not be registered
    assert not event.contains(target, identifier, partial3)
    
    # Register them
    event.listen(target, identifier, partial2)
    event.listen(target, identifier, partial3)
    
    # All should be registered
    assert event.contains(target, identifier, partial1)
    assert event.contains(target, identifier, partial2)
    assert event.contains(target, identifier, partial3)
    
    # Clean up
    event.remove(target, identifier, partial1)
    event.remove(target, identifier, partial2)
    event.remove(target, identifier, partial3)


def test_decorated_functions():
    """Test with decorated functions."""
    target = create_engine('sqlite:///:memory:')
    identifier = 'connect'
    
    def decorator(fn):
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        wrapper.__wrapped__ = fn
        return wrapper
    
    @decorator
    def decorated_function(*args, **kwargs):
        pass
    
    # Register the decorated function
    event.listen(target, identifier, decorated_function)
    assert event.contains(target, identifier, decorated_function)
    
    # The original function should NOT be registered
    if hasattr(decorated_function, '__wrapped__'):
        original = decorated_function.__wrapped__
        assert not event.contains(target, identifier, original)
    
    # Clean up
    event.remove(target, identifier, decorated_function)


def test_method_reference_equality():
    """Test method reference equality issues."""
    target = create_engine('sqlite:///:memory:')
    identifier = 'connect'
    
    class MyClass:
        def method(self, *args, **kwargs):
            pass
    
    obj = MyClass()
    
    # Get two references to the same method
    method_ref1 = obj.method
    method_ref2 = obj.method
    
    # In Python, these might be different objects
    # but refer to the same underlying method
    print(f"method_ref1 is method_ref2: {method_ref1 is method_ref2}")
    
    # Register first reference
    event.listen(target, identifier, method_ref1)
    assert event.contains(target, identifier, method_ref1)
    
    # Check if second reference is considered registered
    # This behavior might vary
    is_ref2_registered = event.contains(target, identifier, method_ref2)
    print(f"Second reference registered: {is_ref2_registered}")
    
    # Try to register second reference
    event.listen(target, identifier, method_ref2)
    assert event.contains(target, identifier, method_ref2)
    
    # Remove using first reference
    event.remove(target, identifier, method_ref1)
    
    # Check if second reference is still registered
    ref2_still_registered = event.contains(target, identifier, method_ref2)
    print(f"Second reference still registered after removing first: {ref2_still_registered}")
    
    # Clean up if needed
    if ref2_still_registered:
        event.remove(target, identifier, method_ref2)


def test_generator_function():
    """Test with generator functions."""
    target = create_engine('sqlite:///:memory:')
    identifier = 'connect'
    
    def generator_function(*args, **kwargs):
        yield 1
        yield 2
        yield 3
    
    # Register a generator function (not a generator object)
    event.listen(target, identifier, generator_function)
    assert event.contains(target, identifier, generator_function)
    
    # Clean up
    event.remove(target, identifier, generator_function)


def test_async_function():
    """Test with async functions."""
    target = create_engine('sqlite:///:memory:')
    identifier = 'connect'
    
    async def async_listener(*args, **kwargs):
        pass
    
    # Try to register an async function
    # SQLAlchemy might not support this
    try:
        event.listen(target, identifier, async_listener)
        assert event.contains(target, identifier, async_listener)
        event.remove(target, identifier, async_listener)
    except Exception as e:
        # Async functions might not be supported
        print(f"Async function failed: {e}")


if __name__ == "__main__":
    print("Testing edge cases...")
    test_method_reference_equality()
    print("\nTesting builtin functions...")
    test_builtin_functions()
    print("\nTesting async functions...")
    test_async_function()