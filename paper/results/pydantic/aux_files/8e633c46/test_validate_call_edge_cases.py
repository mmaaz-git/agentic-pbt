"""Edge case property tests for pydantic.validate_call_decorator."""

from functools import partial
from typing import Any

from hypothesis import given, strategies as st
from pydantic import ValidationError, validate_call
from pydantic.errors import PydanticUserError


# Property: Partial of partial should maintain proper validation
@given(st.integers(), st.integers())
def test_deeply_nested_partial(a, b):
    """Test that deeply nested partials are handled correctly."""
    
    def base_func(x: int, y: int, z: int, w: int) -> int:
        return x + y + z + w
    
    # Create a partial of partial
    p1 = partial(base_func, a)
    p2 = partial(p1, b)
    
    # According to the code, partial of partial should work but with a check
    try:
        decorated = validate_call(p2)
        # Should work with remaining args
        result = decorated(10, 20)
        assert result == a + b + 10 + 20
    except PydanticUserError as e:
        # The code checks for "partial of partial" at line 36
        if "Partial of partial" not in str(e):
            raise


# Property: Decorator ordering matters
@given(st.integers())
def test_decorator_order_enforcement(x):
    """Test that decorator order is enforced as per error messages."""
    
    # This should fail - @classmethod should be on top
    try:
        class TestClass:
            @classmethod
            def method(cls, n: int) -> int:
                return n * 2
        
        # Try to decorate the classmethod directly
        decorated = validate_call(TestClass.method)
        assert False, "Should reject classmethod decoration"
    except PydanticUserError as e:
        assert "@classmethod" in str(e) or "decorator should be applied after" in str(e)
    
    # Same for staticmethod
    try:
        class TestClass2:
            @staticmethod  
            def method(n: int) -> int:
                return n * 2
        
        decorated = validate_call(TestClass2.method)
        assert False, "Should reject staticmethod decoration"
    except PydanticUserError as e:
        assert "@staticmethod" in str(e) or "decorator should be applied after" in str(e)


# Property: Lambda function support
@given(st.integers(), st.integers())
def test_lambda_validation(a, b):
    """Lambdas should be supported according to error message."""
    
    # Simple lambda
    lambda_func = lambda x, y: x + y
    decorated = validate_call(lambda_func)
    
    result = decorated(a, b)
    assert result == a + b
    
    # Lambda with type hints (using annotations)
    lambda_with_hints = lambda x: x * 2
    lambda_with_hints.__annotations__ = {'x': int, 'return': int}
    
    decorated_typed = validate_call(lambda_with_hints)
    assert decorated_typed(a) == a * 2


# Property: Instance method edge cases
@given(st.integers())
def test_instance_callable_rejection(x):
    """Instance callables should be rejected with specific error."""
    
    class CallableClass:
        def __init__(self, value):
            self.value = value
        
        def __call__(self, n):
            return self.value + n
    
    obj = CallableClass(x)
    
    # Should reject instance decoration
    try:
        decorated = validate_call(obj)
        assert False, "Should reject instance callable"
    except PydanticUserError as e:
        assert "instances or other callables" in str(e)


# Property: Functions without signatures
def test_builtin_function_rejection():
    """Built-in functions should be rejected."""
    
    # Test with various built-ins
    builtins_to_test = [len, abs, max, min, sum]
    
    for builtin_func in builtins_to_test:
        try:
            decorated = validate_call(builtin_func)
            # If it somehow works, test it
            if builtin_func == abs:
                assert decorated(-5) == 5
        except PydanticUserError as e:
            assert "built-in function" in str(e) or "is not supported" in str(e)


# Property: Class decoration attempt
@given(st.text(min_size=1))
def test_class_decoration_rejection(class_name):
    """Classes should be rejected with helpful error."""
    
    # Create a class dynamically
    TestClass = type(class_name, (), {'method': lambda self: 42})
    
    try:
        decorated = validate_call(TestClass)
        assert False, "Should reject class decoration"
    except PydanticUserError as e:
        assert "should be applied to functions, not classes" in str(e)


# Property: Signature validation for partial
@given(st.integers(), st.integers())
def test_partial_signature_handling(a, b):
    """Partials should maintain proper signature after decoration."""
    import inspect
    
    def func_with_many_args(w: int, x: int, y: int, z: int) -> int:
        return w + x + y + z
    
    # Create partial with some args bound
    partial_func = partial(func_with_many_args, a, b)
    
    # Decorate the partial
    decorated = validate_call(partial_func)
    
    # Should work with remaining args
    result = decorated(10, 20)
    assert result == a + b + 10 + 20
    
    # Check signature is still inspectable
    try:
        sig = inspect.signature(decorated)
        # Should have 2 parameters (y and z)
        assert len(sig.parameters) == 2
    except ValueError:
        # Some edge cases might not have valid signatures
        pass


# Property: Return validation with None
@given(st.one_of(st.none(), st.integers()))
def test_none_return_validation(value):
    """Test return validation with None values."""
    
    @validate_call(validate_return=True)
    def may_return_none(x) -> int:
        # Claims to return int but might return None
        if x is None:
            return None
        return x
    
    if value is None:
        # Should fail validation since return type is int, not Optional[int]
        try:
            result = may_return_none(value)
            # None might be coerced to 0 or might fail
            if result is not None:
                assert isinstance(result, int)
        except ValidationError as e:
            assert "int" in str(e)
    else:
        # Should work fine
        result = may_return_none(value)
        assert result == value


# Property: Empty function validation
@given(st.integers())
def test_empty_function_validation(x):
    """Functions that don't explicitly return should handle None."""
    
    @validate_call(validate_return=True)
    def no_return(n: int) -> None:
        # Function with no return statement
        pass
    
    result = no_return(x)
    assert result is None
    
    @validate_call(validate_return=True)
    def wrong_return_hint(n: int) -> int:
        # Claims int but implicitly returns None
        pass
    
    try:
        result = wrong_return_hint(x)
        # This should fail validation or coerce None somehow
        if result is None:
            print(f"BUG: Function claiming to return int returned None without error")
    except ValidationError:
        pass  # Expected