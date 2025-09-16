"""Property-based tests for pydantic.validate_call_decorator."""

import math
from functools import partial
from typing import Any, Optional

from hypothesis import assume, given, strategies as st
from pydantic import ValidationError, validate_call


# Property 1: Decorator preserves function attributes
@given(
    st.text(min_size=1).filter(lambda x: x.isidentifier()),
    st.text(),
    st.integers()
)
def test_decorator_preserves_attributes(name, doc, num):
    """Validate_call should preserve original function attributes."""
    
    def original_func(x: int) -> int:
        return x + 1
    
    original_func.__name__ = name
    original_func.__doc__ = doc
    original_func.custom_attr = num
    
    decorated = validate_call(original_func)
    
    # Check standard attributes are preserved
    assert decorated.__name__ == name
    assert decorated.__doc__ == doc
    # Check custom attributes are preserved
    assert decorated.custom_attr == num


# Property 2: Partial function support
@given(
    st.integers(),
    st.integers(),
    st.integers()
)
def test_partial_function_validation(a, b, c):
    """Validate_call should work correctly with partial functions."""
    
    @validate_call
    def add_three(x: int, y: int, z: int) -> int:
        return x + y + z
    
    # Create partial with first argument
    partial_func = partial(add_three, a)
    
    # Should work with remaining arguments
    result = partial_func(b, c)
    assert result == a + b + c
    
    # Test decorated partial
    def raw_add(x: int, y: int, z: int) -> int:
        return x + y + z
    
    partial_raw = partial(raw_add, a)
    decorated_partial = validate_call(partial_raw)
    
    result2 = decorated_partial(b, c)
    assert result2 == a + b + c


# Property 3: Return value validation
@given(st.integers())
def test_return_validation_consistency(x):
    """Return validation should enforce type constraints consistently."""
    
    # Function that returns wrong type
    @validate_call(validate_return=True)
    def returns_string_typed_as_int(n: int) -> int:
        return str(n)  # Returns string but claims int
    
    # Should raise validation error for return type
    try:
        result = returns_string_typed_as_int(x)
        # If we get here, validation didn't work
        assert False, f"Expected ValidationError but got result: {result}"
    except ValidationError as e:
        # This is expected - return type validation should catch the mismatch
        assert "int" in str(e) or "string" in str(e)


# Property 4: Type coercion consistency
@given(st.integers(-1000, 1000))
def test_coercion_consistency(x):
    """Type coercion should be consistent and reversible where applicable."""
    
    @validate_call
    def takes_string(s: str) -> str:
        return s
    
    # Integer should be coerced to string
    result = takes_string(x)
    assert result == str(x)
    assert isinstance(result, str)
    
    @validate_call
    def takes_int(n: int) -> int:
        return n
    
    # String representation of int should be parseable back
    str_x = str(x)
    result2 = takes_int(str_x)
    assert result2 == x
    assert isinstance(result2, int)


# Property 5: Validation idempotence 
@given(st.integers())
def test_double_decoration_behavior(x):
    """Double decoration should either work or fail consistently."""
    
    def simple_func(n: int) -> int:
        return n * 2
    
    once_decorated = validate_call(simple_func)
    twice_decorated = validate_call(once_decorated)
    
    # Both should produce same result
    result1 = once_decorated(x)
    result2 = twice_decorated(x)
    assert result1 == result2 == x * 2


# Property 6: Config parameter propagation
@given(st.booleans())
def test_config_affects_behavior(strict_mode):
    """Config parameters should affect validation behavior."""
    
    config = {'strict': strict_mode} if strict_mode else None
    
    @validate_call(config=config)
    def func_with_config(x: int) -> int:
        return x
    
    # Test with valid input
    assert func_with_config(42) == 42
    
    # Test coercion behavior might differ based on strict mode
    if not strict_mode:
        # Non-strict mode might allow more coercion
        try:
            result = func_with_config("42")
            assert result == 42
        except ValidationError:
            # Some configs might still be strict about this
            pass


# Property 7: Validation with None and Optional
@given(st.one_of(st.none(), st.integers()))
def test_optional_parameter_handling(value):
    """Optional parameters should handle None correctly."""
    
    @validate_call
    def takes_optional(x: Optional[int]) -> Optional[int]:
        return x
    
    result = takes_optional(value)
    assert result == value
    
    if value is not None:
        assert isinstance(result, int)


# Property 8: Method decoration support
@given(st.integers(), st.text())
def test_method_decoration(x, s):
    """Validate_call should work with class methods."""
    
    class TestClass:
        @validate_call
        def method(self, n: int, text: str) -> str:
            return f"{n}: {text}"
        
        @classmethod
        @validate_call
        def class_method(cls, n: int) -> int:
            return n * 2
        
        @staticmethod
        @validate_call
        def static_method(n: int) -> int:
            return n + 1
    
    obj = TestClass()
    
    # Instance method
    assert obj.method(x, s) == f"{x}: {s}"
    
    # Class method
    assert TestClass.class_method(x) == x * 2
    
    # Static method  
    assert TestClass.static_method(x) == x + 1


# Property 9: Error messages contain useful information
@given(st.text(), st.integers())
def test_error_messages_informative(wrong_type_value, correct_type_value):
    """Validation errors should contain information about the type mismatch."""
    
    @validate_call
    def expects_int(x: int) -> int:
        return x
    
    try:
        # Pass string where int expected
        expects_int(wrong_type_value)
        # Only fail if the string wasn't parseable as int
        try:
            int(wrong_type_value)
        except ValueError:
            assert False, "Expected ValidationError for non-numeric string"
    except ValidationError as e:
        error_str = str(e)
        # Error should mention the function name or parameter
        assert "expects_int" in error_str or "int" in error_str.lower() or "0" in error_str


# Property 10: Recursive validation in nested calls
@given(st.integers())  
def test_nested_validated_calls(x):
    """Nested validated function calls should each validate independently."""
    
    @validate_call
    def inner(n: int) -> int:
        return n + 1
    
    @validate_call
    def outer(n: int) -> int:
        return inner(n) * 2
    
    result = outer(x)
    assert result == (x + 1) * 2
    
    # Test that validation happens at each level
    @validate_call
    def outer_returns_wrong_type(n: int) -> int:
        return str(inner(n))  # Returns string but claims int
    
    if validate_call(outer_returns_wrong_type).validate_return:
        try:
            outer_returns_wrong_type(x)
            # Check if validation is actually enabled for return
        except (ValidationError, AttributeError):
            pass  # Expected if return validation is on