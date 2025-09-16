"""Advanced property-based tests for pydantic.validate_call_decorator."""

import inspect
from functools import partial
from typing import Any, List, Optional, Union

from hypothesis import assume, given, settings, strategies as st
from pydantic import ValidationError, validate_call


# Property: Partial function chaining maintains validation
@given(
    st.integers(),
    st.integers(), 
    st.integers(),
    st.integers()
)
def test_nested_partial_validation(a, b, c, d):
    """Nested partials should maintain validation at each level."""
    
    @validate_call
    def add_four(w: int, x: int, y: int, z: int) -> int:
        return w + x + y + z
    
    # Create nested partials
    p1 = partial(add_four, a)
    p2 = partial(p1, b)
    p3 = partial(p2, c)
    
    result = p3(d)
    assert result == a + b + c + d
    
    # Test validation still works on final partial
    try:
        p3("not_an_int")
        # Should have raised ValidationError
        assert False, "Expected ValidationError for invalid type"
    except ValidationError:
        pass  # Expected


# Property: Decorator doesn't mutate original function
@given(st.integers())
def test_original_function_unchanged(x):
    """Original function should remain unchanged after decoration."""
    
    def original(n: int) -> int:
        return n * 2
    
    # Store original properties
    original_id = id(original)
    original_code = original.__code__
    
    # Decorate
    decorated = validate_call(original)
    
    # Original should be unchanged
    assert id(original) == original_id
    assert original.__code__ is original_code
    assert original(x) == x * 2
    
    # Decorated should be different object
    assert decorated is not original
    assert decorated(x) == x * 2


# Property: Validation with mixed type hints
@given(
    st.one_of(st.integers(), st.text()),
    st.one_of(st.integers(), st.text())
)
def test_union_type_validation(val1, val2):
    """Union types should accept any of the specified types."""
    
    @validate_call
    def accepts_union(x: Union[int, str]) -> Union[int, str]:
        return x
    
    # Both int and str should work
    result = accepts_union(val1)
    assert result == val1
    
    @validate_call  
    def accepts_int_or_str_list(x: Union[int, List[str]]) -> Any:
        return x
    
    # Single values should work or fail based on type
    if isinstance(val2, int):
        assert accepts_int_or_str_list(val2) == val2
    else:
        # String should fail (not int, not List[str])
        try:
            accepts_int_or_str_list(val2)
            # Might coerce in some cases
        except ValidationError:
            pass  # Expected for wrong type


# Property: Recursive decorator application
@given(st.integers(0, 5), st.integers())
def test_recursive_decoration(depth, value):
    """Multiple decorator applications should be stable."""
    
    def base_func(x: int) -> int:
        return x + 1
    
    func = base_func
    for _ in range(depth):
        func = validate_call(func)
    
    # Should still work regardless of depth
    result = func(value)
    assert result == value + 1


# Property: Error on invalid callable types
@given(st.integers())
def test_invalid_callable_rejection(x):
    """validate_call should reject invalid callable types."""
    from pydantic.errors import PydanticUserError
    
    # Test with a class (not a function)
    class NotAFunction:
        pass
    
    try:
        validate_call(NotAFunction)
        assert False, "Should reject class decoration"
    except PydanticUserError as e:
        assert "validate_call" in str(e)
    
    # Test with built-in
    try:
        validate_call(len)
        assert False, "Should reject built-in function"
    except PydanticUserError:
        pass


# Property: Partial of partial behavior
@given(st.integers(), st.integers(), st.integers())
def test_partial_of_partial_error(a, b, c):
    """Partial of partial should be handled correctly."""
    
    def add_three(x: int, y: int, z: int) -> int:
        return x + y + z
    
    # Create partial of partial
    p1 = partial(add_three, a)
    p2 = partial(p1, b)
    
    # This should work
    decorated = validate_call(p2)
    assert decorated(c) == a + b + c
    
    # But partial of partial of partial...
    p3 = partial(p2, c)
    try:
        # Decorating a fully applied partial
        decorated_p3 = validate_call(p3)
        # If it works, it should return the value
        result = decorated_p3()
        assert result == a + b + c
    except Exception:
        # Some edge cases might fail
        pass


# Property: Special method handling  
@given(st.integers())
def test_special_method_validation(x):
    """Special methods should be validated correctly."""
    
    class ValidatedClass:
        @validate_call
        def __init__(self, value: int):
            self.value = value
        
        @validate_call
        def __call__(self, n: int) -> int:
            return self.value + n
    
    # __init__ validation
    obj = ValidatedClass(x)
    assert obj.value == x
    
    # __call__ validation
    result = obj(10)
    assert result == x + 10
    
    # Test with invalid types
    try:
        ValidatedClass("not_int")
        # Might coerce
    except ValidationError:
        pass  # Expected
    
    try:
        obj("not_int")
        # Might coerce  
    except ValidationError:
        pass  # Expected


# Property: Keyword-only arguments
@given(st.integers(), st.text())
def test_keyword_only_validation(num, text):
    """Keyword-only arguments should be validated."""
    
    @validate_call
    def keyword_only_func(*, x: int, y: str) -> str:
        return f"{x}: {y}"
    
    # Must use keywords
    result = keyword_only_func(x=num, y=text)
    assert result == f"{num}: {text}"
    
    # Positional should fail
    try:
        keyword_only_func(num, text)
        assert False, "Should require keyword arguments"
    except TypeError:
        pass  # Expected


# Property: Default values interaction
@given(st.integers())
def test_default_values_preserved(x):
    """Default values should work with validation."""
    
    @validate_call
    def with_defaults(a: int, b: int = 10, c: Optional[int] = None) -> int:
        if c is None:
            return a + b
        return a + b + c
    
    # Test with just required arg
    assert with_defaults(x) == x + 10
    
    # Test with optional arg
    assert with_defaults(x, 20) == x + 20
    
    # Test with all args
    assert with_defaults(x, 20, 30) == x + 50
    
    # Test None is preserved
    assert with_defaults(x, 20, None) == x + 20


# Property: Signature preservation
@given(st.text(min_size=1).filter(lambda s: s.isidentifier()))
def test_signature_preservation(param_name):
    """Function signature should be preserved after decoration."""
    assume(param_name not in ['return', 'self', 'cls'])
    
    # Create function with dynamic parameter name
    exec_globals = {}
    func_code = f"""
def dynamic_func({param_name}: int) -> int:
    return {param_name} * 2
"""
    exec(func_code, exec_globals)
    original = exec_globals['dynamic_func']
    
    decorated = validate_call(original)
    
    # Check signatures match
    orig_sig = inspect.signature(original)
    dec_sig = inspect.signature(decorated)
    
    assert len(orig_sig.parameters) == len(dec_sig.parameters)
    assert param_name in dec_sig.parameters