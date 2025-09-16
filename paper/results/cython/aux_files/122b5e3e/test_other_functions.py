import Cython.Shadow as cs
from hypothesis import given, strategies as st, assume
import pytest


@given(st.one_of(st.integers(), st.floats(allow_nan=False), st.text()))
def test_cast_with_typedef(value):
    """Test cast function with typedef types"""
    # Create a typedef
    MyInt = cs.typedef(int)
    
    # Cast to typedef should work
    result = cs.cast(MyInt, value)
    
    # If value is already an int, it should be preserved
    if isinstance(value, int):
        assert result == value
    # Otherwise it should be converted
    elif isinstance(value, (float, str)):
        try:
            expected = int(value)
            assert result == expected
        except (ValueError, OverflowError):
            pass  # Conversion might fail for some values


@given(st.lists(st.integers()))
def test_cast_none_handling(lst):
    """Test that cast handles None correctly"""
    # According to the code, cast should handle None specially
    result = cs.cast(list, None)
    assert result is None
    
    # Non-None should be passed through or converted
    result = cs.cast(list, lst)
    assert result == lst


@given(st.integers())
def test_pointer_and_address(value):
    """Test pointer creation and dereferencing"""
    # Create a pointer to the value
    ptr = cs.address(value)
    
    # Should be able to dereference it
    assert ptr[0] == value
    
    # Test creating pointer type directly
    IntPointer = cs.pointer(int)
    ptr2 = IntPointer([value])
    assert ptr2[0] == value


@given(st.lists(st.integers(), min_size=1, max_size=10))
def test_array_type(values):
    """Test array type creation"""
    # Create an array type
    IntArray = cs.array(int, len(values))
    
    # Create an array instance
    arr = IntArray(values)
    
    # Should be able to access elements
    for i, val in enumerate(values):
        assert arr[i] == val


@given(st.integers(), st.integers())
def test_cpow_function(base, exp):
    """Test cpow function if it exists"""
    if not hasattr(cs, 'cpow'):
        pytest.skip("cpow not available")
    
    assume(-100 < base < 100)  # Avoid overflow
    assume(-10 < exp < 10)    # Avoid overflow
    
    result = cs.cpow(base, exp)
    expected = base ** exp
    
    # For integer inputs, should match
    assert result == expected


@given(st.one_of(st.integers(), st.floats(allow_nan=False)))
def test_declare_function(value):
    """Test declare function for creating typed variables"""
    # Declare a variable with a type
    result = cs.declare(int, value)
    
    # For integers, should preserve value
    if isinstance(value, int):
        assert result == value
    # For floats, should convert to int
    elif isinstance(value, float):
        assert result == int(value)


@given(st.integers())
def test_const_types(value):
    """Test const type creation"""
    # const_int should behave like int
    const_val = cs.const_int(value)
    assert const_val == value
    
    # Should be able to create const pointer types
    const_ptr = cs.p_const_int([value])
    assert const_ptr[0] == value


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])