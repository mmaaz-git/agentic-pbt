"""Focused test for return validation behavior."""

from hypothesis import given, strategies as st
from pydantic import ValidationError, validate_call


# Test: Functions with wrong return type but no actual return
@given(st.integers())
def test_implicit_none_return_validation(x):
    """Functions that implicitly return None but claim other types."""
    
    @validate_call(validate_return=True)
    def claims_int_returns_none(n: int) -> int:
        # Function claims to return int but has no return statement
        # This implicitly returns None
        pass
    
    # This should raise ValidationError since None is not int
    # But let's see what actually happens
    try:
        result = claims_int_returns_none(x)
        # If we get here without error, check what was returned
        assert result is None, f"Expected None, got {result}"
        # This is a bug - function claiming int returned None without validation error
        print(f"BUG FOUND: Function with '-> int' returned None without ValidationError")
        return False  # Indicate bug found
    except ValidationError as e:
        # This is the expected behavior
        assert "int" in str(e).lower() or "none" in str(e).lower()
        return True  # Correct behavior


# Test: Explicit None return when expecting int
@given(st.integers())  
def test_explicit_none_return_validation(x):
    """Functions that explicitly return None but claim other types."""
    
    @validate_call(validate_return=True)
    def explicitly_returns_none(n: int) -> int:
        # Function claims to return int but explicitly returns None
        return None
    
    try:
        result = explicitly_returns_none(x)
        # If we get here without error, it's a problem
        assert result is None, f"Expected None, got {result}"
        print(f"BUG: Function with '-> int' returned None without ValidationError")
        return False
    except ValidationError as e:
        # Expected behavior
        return True


# Test: String to int coercion in return
@given(st.integers(-1000, 1000))
def test_return_type_coercion(x):
    """Test if return values are coerced like input values are."""
    
    @validate_call(validate_return=True)
    def returns_string_of_int(n: int) -> int:
        # Returns string representation of number
        return str(n)
    
    result = returns_string_of_int(x)
    
    # Check what type was actually returned
    if isinstance(result, str):
        print(f"BUG: Function claiming '-> int' returned str without coercion")
        return False
    elif isinstance(result, int):
        # It was coerced - verify it's correct value
        assert result == x
        # This is debatable - is coercion expected or a bug?
        # Based on Pydantic's philosophy, this might be intended
        return True


# Run the focused tests
if __name__ == "__main__":
    print("Testing return validation edge cases...")
    
    # Test 1: Implicit None
    print("\n1. Testing implicit None return:")
    test_implicit_none_return_validation(42)
    
    # Test 2: Explicit None  
    print("\n2. Testing explicit None return:")
    test_explicit_none_return_validation(42)
    
    # Test 3: Type coercion
    print("\n3. Testing return type coercion:")
    test_return_type_coercion(42)