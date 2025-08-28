import math
from hypothesis import given, strategies as st, assume, settings
import fire.test_components_py3 as components
import pytest


# Test WithTypes.double property
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_with_types_double(x):
    """Test that WithTypes.double returns input multiplied by 2."""
    obj = components.WithTypes()
    result = obj.double(x)
    assert math.isclose(result, 2 * x, rel_tol=1e-9)


# Test WithDefaultsAndTypes.double property
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_with_defaults_and_types_double(x):
    """Test that WithDefaultsAndTypes.double returns input multiplied by 2."""
    obj = components.WithDefaultsAndTypes()
    result = obj.double(x)
    assert math.isclose(result, 2 * x, rel_tol=1e-9)


# Test KeywordOnly.double property
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_keyword_only_double(x):
    """Test that KeywordOnly.double returns count multiplied by 2."""
    obj = components.KeywordOnly()
    result = obj.double(count=x)
    assert math.isclose(result, 2 * x, rel_tol=1e-9)


# Test KeywordOnly.triple property
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_keyword_only_triple(x):
    """Test that KeywordOnly.triple returns count multiplied by 3."""
    obj = components.KeywordOnly()
    result = obj.triple(count=x)
    assert math.isclose(result, 3 * x, rel_tol=1e-9)


# Test WithDefaultsAndTypes.get_int property
@given(st.one_of(st.none(), st.integers(min_value=-1000000, max_value=1000000)))
def test_get_int_behavior(value):
    """Test get_int returns 0 for None, otherwise returns the value."""
    obj = components.WithDefaultsAndTypes()
    result = obj.get_int(value)
    if value is None:
        assert result == 0
    else:
        assert result == value


# Test LRU cache idempotence
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False),
    st.text(),
    st.lists(st.integers())
))
def test_lru_cache_idempotence(x):
    """Test that lru_cache_decorated returns same result for same input."""
    result1 = components.lru_cache_decorated(x)
    result2 = components.lru_cache_decorated(x)
    assert result1 == result2
    assert result1 == x  # Also test it returns the input


# Test LruCacheDecoratedMethod idempotence
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False),
    st.text(),
    st.lists(st.integers())
))
def test_lru_cache_method_idempotence(x):
    """Test that LruCacheDecoratedMethod returns same result for same input."""
    obj = components.LruCacheDecoratedMethod()
    result1 = obj.lru_cache_in_class(x)
    result2 = obj.lru_cache_in_class(x)
    assert result1 == result2
    assert result1 == x  # Also test it returns the input


# Test identity function round-trip property
@given(
    st.integers(),
    st.integers(),
    st.integers(),
    st.integers(),
    st.lists(st.integers(), max_size=5),
    st.integers(),
    st.integers(),
    st.integers(),
    st.integers(),
    st.dictionaries(st.text(min_size=1), st.integers(), max_size=3)
)
def test_identity_round_trip(arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8, arg9, arg10):
    """Test that identity returns all arguments unchanged."""
    result = components.identity(
        arg1, arg2, arg3, arg4, *arg5,
        arg6=arg6, arg7=arg7, arg8=arg8, arg9=arg9, **arg10
    )
    
    assert result[0] == arg1
    assert result[1] == arg2
    assert result[2] == arg3
    assert result[3] == arg4
    assert result[4] == tuple(arg5)
    assert result[5] == arg6
    assert result[6] == arg7
    assert result[7] == arg8
    assert result[8] == arg9
    assert result[9] == arg10


# Test HelpTextComponent.identity
@given(st.text(), st.text())
def test_help_text_identity(alpha, beta):
    """Test that HelpTextComponent.identity returns arguments unchanged."""
    obj = components.HelpTextComponent()
    result = obj.identity(alpha=alpha, beta=beta)
    assert result == (alpha, beta)


# Test WithDefaultsAndTypes.double with default value
def test_with_defaults_double_default():
    """Test that WithDefaultsAndTypes.double uses default value of 0."""
    obj = components.WithDefaultsAndTypes()
    result = obj.double()
    assert result == 0.0  # 2 * 0 = 0