import math
from decimal import Decimal
from hypothesis import given, strategies as st, assume
import troposphere.supportapp as mod
import pytest


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_float_equivalence_inconsistency(x):
    """Test that floats equal to 1 or 0 are accepted, revealing implementation inconsistency."""
    if x == 1.0:
        assert mod.boolean(x) is True
        # String "1.0" should raise ValueError since it's not in the accepted list
        with pytest.raises(ValueError):
            mod.boolean(str(x))
    elif x == 0.0:
        assert mod.boolean(x) is False
        # String "0.0" should raise ValueError since it's not in the accepted list
        with pytest.raises(ValueError):
            mod.boolean(str(x))
    else:
        with pytest.raises(ValueError):
            mod.boolean(x)


def raises_value_error(x):
    """Helper to check if a value raises ValueError."""
    try:
        mod.boolean(x)
        return False
    except ValueError:
        return True


@given(st.one_of(
    st.just(True), st.just(False),
    st.just(1), st.just(0),
    st.just("1"), st.just("0"),
    st.just("true"), st.just("false"),
    st.just("True"), st.just("False")
))
def test_idempotence(x):
    """Test that boolean(boolean(x)) == boolean(x) for valid inputs."""
    result = mod.boolean(x)
    assert mod.boolean(result) == result
    assert isinstance(result, bool)


@given(st.text(min_size=1, max_size=10))
def test_case_sensitivity(s):
    """Test that the function is case-sensitive for string boolean values."""
    lower = s.lower()
    upper = s.upper()
    
    if lower == "true":
        if s == "true" or s == "True":
            assert mod.boolean(s) is True
        else:
            with pytest.raises(ValueError):
                mod.boolean(s)
    
    elif lower == "false":  
        if s == "false" or s == "False":
            assert mod.boolean(s) is False
        else:
            with pytest.raises(ValueError):
                mod.boolean(s)


@given(st.one_of(
    st.floats(min_value=0.99, max_value=1.01),
    st.floats(min_value=-0.01, max_value=0.01),
    st.decimals(min_value=Decimal('0.99'), max_value=Decimal('1.01')),
    st.decimals(min_value=Decimal('-0.01'), max_value=Decimal('0.01')),
    st.complex_numbers(max_magnitude=2)
))
def test_numeric_type_equality_loophole(x):
    """Test that any numeric type equal to 1 or 0 is accepted, not just int."""
    if x == 1:
        assert mod.boolean(x) is True
    elif x == 0:
        assert mod.boolean(x) is False
    else:
        with pytest.raises(ValueError):
            mod.boolean(x)


@given(st.lists(st.integers(), min_size=0, max_size=1))
def test_container_types_with_equality(container):
    """Test that containers are not accepted even if they might equal numeric values."""
    with pytest.raises(ValueError):
        mod.boolean(container)


@given(st.one_of(
    st.just(1.0),
    st.just(0.0),
    st.just(complex(1, 0)),
    st.just(complex(0, 0))
))
def test_undocumented_numeric_acceptance(x):
    """Test that numeric types not in the explicit list are still accepted."""
    if x == 1:
        assert mod.boolean(x) is True
    elif x == 0:
        assert mod.boolean(x) is False