"""
Pyramid-like decorator module implementation for testing.
Based on common decorator patterns from the Pyramid web framework.
"""

import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

F = TypeVar('F', bound=Callable[..., Any])


class reify:
    """
    A property-like decorator that caches the result of a method call.
    
    This is similar to @property but the function is only called once.
    After the first call, the returned value is cached and reused.
    The cached value becomes an instance attribute with the same name.
    """
    
    def __init__(self, func: Callable) -> None:
        self.func = func
        self.__doc__ = func.__doc__
        self.__name__ = func.__name__
        self.__module__ = func.__module__
        
    def __get__(self, inst: Any, owner: type) -> Any:
        if inst is None:
            return self
        val = self.func(inst)
        setattr(inst, self.__name__, val)
        return val


class Decorator:
    """
    Base class for creating decorators that can be composed and configured.
    """
    
    def __init__(self, **settings):
        self.settings = settings
        self._callbacks = []
        
    def add_callback(self, callback: Callable) -> None:
        """Add a callback to be executed when the decorator is applied."""
        self._callbacks.append(callback)
        
    def __call__(self, wrapped: F) -> F:
        """Apply the decorator to a function."""
        @functools.wraps(wrapped)
        def wrapper(*args, **kwargs):
            # Execute callbacks before the wrapped function
            for callback in self._callbacks:
                callback(wrapped, args, kwargs)
            
            # Call the wrapped function
            result = wrapped(*args, **kwargs)
            
            # Apply any post-processing based on settings
            if self.settings.get('json_response'):
                import json
                result = json.dumps(result)
            
            return result
        
        # Store metadata about the decoration
        wrapper.__decorator_settings__ = self.settings
        wrapper.__wrapped_function__ = wrapped
        
        return wrapper


def view_config(**settings) -> Callable[[F], F]:
    """
    Decorator for configuring views in a Pyramid-like fashion.
    
    Parameters:
    - route_name: The name of the route this view should be associated with
    - renderer: The renderer to use (e.g., 'json', 'string', template name)
    - request_method: HTTP method(s) this view responds to
    - permission: Required permission to access this view
    """
    def decorator(func: F) -> F:
        # Store configuration on the function
        if not hasattr(func, '__view_settings__'):
            func.__view_settings__ = []
        func.__view_settings__.append(settings)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Simulate view processing
            result = func(*args, **kwargs)
            
            # Apply renderer if specified
            renderer = settings.get('renderer')
            if renderer == 'json':
                import json
                if not isinstance(result, str):
                    result = json.dumps(result)
            elif renderer == 'string':
                result = str(result)
                
            return result
            
        wrapper.__view_settings__ = func.__view_settings__
        return wrapper
        
    return decorator


def subscriber(*interfaces) -> Callable[[F], F]:
    """
    Decorator to mark a function as an event subscriber.
    
    The decorated function will be registered to receive events
    of the specified interface types.
    """
    def decorator(func: F) -> F:
        # Mark the function as a subscriber
        func.__subscriber_interfaces__ = interfaces
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # In a real implementation, this would be called by the event system
            return func(*args, **kwargs)
            
        wrapper.__subscriber_interfaces__ = interfaces
        return wrapper
        
    return decorator


class cached_property:
    """
    A property that is only computed once per instance and then caches
    the computed value for the lifetime of the instance.
    
    Similar to reify but follows Python's property protocol more closely.
    """
    
    def __init__(self, func: Callable) -> None:
        self.func = func
        functools.update_wrapper(self, func)
        
    def __get__(self, obj: Any, owner: type = None) -> Any:
        if obj is None:
            return self
            
        # Check if value is already cached
        cache_attr = f'_cached_{self.func.__name__}'
        if hasattr(obj, cache_attr):
            return getattr(obj, cache_attr)
            
        # Compute and cache the value
        value = self.func(obj)
        setattr(obj, cache_attr, value)
        return value
        
    def __set__(self, obj: Any, value: Any) -> None:
        # Allow setting the cached value directly
        cache_attr = f'_cached_{self.func.__name__}'
        setattr(obj, cache_attr, value)
        
    def __delete__(self, obj: Any) -> None:
        # Clear the cached value
        cache_attr = f'_cached_{self.func.__name__}'
        if hasattr(obj, cache_attr):
            delattr(obj, cache_attr)


def preserve_signature(wrapped: Callable) -> Callable[[F], F]:
    """
    Decorator that preserves the original function's signature.
    
    This is useful when creating decorators that modify function behavior
    but should maintain the same signature for introspection.
    """
    def decorator(wrapper: F) -> F:
        # Copy signature from wrapped to wrapper
        wrapper.__signature__ = inspect.signature(wrapped)
        wrapper.__annotations__ = wrapped.__annotations__
        
        # Preserve other metadata
        functools.update_wrapper(wrapper, wrapped)
        
        return wrapper
        
    return decorator


def compose(*decorators: Callable) -> Callable[[F], F]:
    """
    Compose multiple decorators into a single decorator.
    
    Decorators are applied in the order given, so:
    compose(a, b, c)(func) is equivalent to a(b(c(func)))
    """
    def decorator(func: F) -> F:
        result = func
        for dec in reversed(decorators):
            result = dec(result)
        return result
    return decorator


class MethodDecorator:
    """
    A decorator that can be applied to both instance and class methods.
    
    It properly handles the 'self' or 'cls' parameter based on the context.
    """
    
    def __init__(self, func: Optional[Callable] = None, **options):
        self.func = func
        self.options = options
        
    def __call__(self, *args, **kwargs):
        if self.func is None:
            # Used with parameters: @MethodDecorator(option=value)
            self.func = args[0]
            return self
        else:
            # Direct decoration: @MethodDecorator
            return self.func(*args, **kwargs)
            
    def __get__(self, obj, objtype=None):
        if obj is None:
            # Accessed from class
            return functools.partial(self.func, objtype)
        # Accessed from instance
        return functools.partial(self.func, obj)


def validate_arguments(**validators: Dict[str, Callable]) -> Callable[[F], F]:
    """
    Decorator that validates function arguments before execution.
    
    Parameters:
    - validators: A dict mapping argument names to validation functions
    """
    def decorator(func: F) -> F:
        sig = inspect.signature(func)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Bind arguments to their names
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            
            # Validate each argument that has a validator
            for arg_name, validator in validators.items():
                if arg_name in bound.arguments:
                    value = bound.arguments[arg_name]
                    if not validator(value):
                        raise ValueError(f"Invalid value for {arg_name}: {value}")
                        
            return func(*args, **kwargs)
            
        return wrapper
    return decorator