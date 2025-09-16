"""Additional property-based tests for more components."""

import math
from hypothesis import given, strategies as st, settings, assume
import fire.test_components as tc


@given(
    count=st.one_of(
        st.integers(min_value=-10000, max_value=10000),
        st.floats(allow_nan=False, allow_infinity=False)
    )
)
def test_with_defaults_double_property(count):
    """Test that WithDefaults.double correctly doubles the input."""
    wd = tc.WithDefaults()
    result = wd.double(count)
    expected = 2 * count
    
    if isinstance(result, float) or isinstance(expected, float):
        assert math.isclose(result, expected, rel_tol=1e-9)
    else:
        assert result == expected


@given(
    count=st.one_of(
        st.integers(min_value=-10000, max_value=10000),
        st.floats(allow_nan=False, allow_infinity=False)
    )
)
def test_with_defaults_triple_property(count):
    """Test that WithDefaults.triple correctly triples the input."""
    wd = tc.WithDefaults()
    result = wd.triple(count)
    expected = 3 * count
    
    if isinstance(result, float) or isinstance(expected, float):
        assert math.isclose(result, expected, rel_tol=1e-9)
    else:
        assert result == expected


def test_with_defaults_double_default():
    """Test that WithDefaults.double() returns 0 by default."""
    wd = tc.WithDefaults()
    assert wd.double() == 0


def test_with_defaults_triple_default():
    """Test that WithDefaults.triple() returns 0 by default."""
    wd = tc.WithDefaults()
    assert wd.triple() == 0


@given(string=st.text())
def test_with_defaults_text_returns_input(string):
    """Test that WithDefaults.text returns the input string."""
    wd = tc.WithDefaults()
    result = wd.text(string)
    assert result == string


def test_with_defaults_text_default():
    """Test the default value of WithDefaults.text()."""
    wd = tc.WithDefaults()
    result = wd.text()
    expected = ('0001020304050607080910111213141516171819'
                '2021222324252627282930313233343536373839')
    assert result == expected


@given(
    alpha=st.one_of(
        st.integers(min_value=-1000, max_value=1000),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000)
    ),
    beta=st.one_of(
        st.integers(min_value=-1000, max_value=1000),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000)
    )
)
def test_mixed_defaults_sum_formula(alpha, beta):
    """Test that MixedDefaults.sum follows the formula alpha + 2*beta."""
    md = tc.MixedDefaults()
    result = md.sum(alpha, beta)
    expected = alpha + 2 * beta
    
    if isinstance(result, float) or isinstance(expected, float):
        assert math.isclose(result, expected, rel_tol=1e-9)
    else:
        assert result == expected


def test_mixed_defaults_sum_defaults():
    """Test default values for MixedDefaults.sum."""
    md = tc.MixedDefaults()
    assert md.sum() == 0  # 0 + 2*0
    assert md.sum(5) == 5  # 5 + 2*0
    assert md.sum(beta=3) == 6  # 0 + 2*3


def test_mixed_defaults_ten():
    """Test that MixedDefaults.ten() always returns 10."""
    md = tc.MixedDefaults()
    assert md.ten() == 10


@given(
    alpha=st.one_of(
        st.integers(),
        st.text(),
        st.floats(allow_nan=False),
        st.lists(st.integers()),
        st.none()
    ),
    beta=st.one_of(
        st.integers(),
        st.text(),
        st.floats(allow_nan=False),
        st.lists(st.integers()),
        st.none()
    )
)
def test_mixed_defaults_identity_returns_tuple(alpha, beta):
    """Test that MixedDefaults.identity returns inputs as tuple."""
    md = tc.MixedDefaults()
    result = md.identity(alpha, beta)
    assert result == (alpha, beta)


@given(
    alpha=st.one_of(
        st.integers(),
        st.text(),
        st.none()
    )
)
def test_mixed_defaults_identity_default_beta(alpha):
    """Test that MixedDefaults.identity has '0' as default for beta."""
    md = tc.MixedDefaults()
    result = md.identity(alpha)
    assert result == (alpha, '0')


@given(
    double_triple_inputs=st.lists(
        st.tuples(
            st.sampled_from(['double', 'triple']),
            st.integers(min_value=-100, max_value=100)
        ),
        min_size=2,
        max_size=10
    )
)
def test_with_defaults_double_triple_relationship(double_triple_inputs):
    """Test relationship: triple(x) = double(x) + x."""
    wd = tc.WithDefaults()
    
    for operation, value in double_triple_inputs:
        double_result = wd.double(value)
        triple_result = wd.triple(value)
        
        # Mathematical relationship: triple(x) = double(x) + x
        assert triple_result == double_result + value
        
        # Also: triple(x) = 1.5 * double(x)
        assert triple_result == 1.5 * double_result


def test_error_raiser_fail():
    """Test that ErrorRaiser.fail() raises ValueError."""
    er = tc.ErrorRaiser()
    try:
        er.fail()
        assert False, "Expected ValueError to be raised"
    except ValueError as e:
        assert str(e) == 'This error is part of a test.'


@given(st.data())
def test_non_comparable_equality_always_raises(data):
    """Test that NonComparable always raises on equality comparison."""
    nc = tc.NonComparable()
    
    # Generate various objects to compare against
    other = data.draw(st.one_of(
        st.integers(),
        st.text(),
        st.none(),
        st.just(tc.NonComparable()),
        st.just(nc)  # Even comparing with itself
    ))
    
    # Both == and != should raise
    try:
        nc == other
        assert False, "Expected ValueError for =="
    except ValueError as e:
        assert str(e) == 'Instances of this class cannot be compared.'
    
    try:
        nc != other
        assert False, "Expected ValueError for !="
    except ValueError as e:
        assert str(e) == 'Instances of this class cannot be compared.'