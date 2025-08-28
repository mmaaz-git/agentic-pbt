"""Additional property-based tests for fire.test_components module"""

import math
from hypothesis import given, strategies as st, assume, settings
import fire.test_components as target


@given(x=st.integers(), y=st.integers())
def test_namedtuple_point_properties(x, y):
    """Test NamedTuplePoint behaves as a proper namedtuple."""
    point = target.NamedTuplePoint(x, y)
    
    # Test field access
    assert point.x == x
    assert point.y == y
    
    # Test tuple properties
    assert point[0] == x
    assert point[1] == y
    assert len(point) == 2
    
    # Test immutability - namedtuples are immutable
    try:
        point.x = x + 1
        assert False, "NamedTuple should be immutable"
    except AttributeError:
        pass  # Expected
    
    # Test equality
    point2 = target.NamedTuplePoint(x, y)
    assert point == point2
    
    # Test unpacking
    a, b = point
    assert a == x
    assert b == y


@given(x=st.integers(min_value=-1000, max_value=1000), 
       y=st.integers(min_value=-1000, max_value=1000))
def test_subpoint_coordinate_sum(x, y):
    """Test SubPoint.coordinate_sum method."""
    point = target.SubPoint(x, y)
    
    # Test inherited properties
    assert point.x == x
    assert point.y == y
    
    # Test coordinate_sum method
    result = point.coordinate_sum()
    assert result == x + y
    
    # Mathematical property: sum is commutative
    point2 = target.SubPoint(y, x)
    assert point2.coordinate_sum() == result


@given(kwargs=st.dictionaries(st.text(min_size=1), st.integers()))
def test_kwargs_props_identity(kwargs):
    """Test Kwargs.props returns the exact kwargs passed."""
    obj = target.Kwargs()
    result = obj.props(**kwargs)
    assert result == kwargs


@given(kwargs=st.dictionaries(
    st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1), 
    st.integers()
))
def test_kwargs_upper_property(kwargs):
    """Test Kwargs.upper returns sorted uppercase keys."""
    obj = target.Kwargs()
    result = obj.upper(**kwargs)
    
    # Result should be uppercase sorted keys joined by space
    expected = ' '.join(sorted(kwargs.keys())).upper()
    assert result == expected


@given(
    positional=st.integers(),
    named=st.one_of(st.none(), st.integers()),
    kwargs=st.dictionaries(st.text(min_size=1), st.integers())
)
def test_kwargs_run_property(positional, named, kwargs):
    """Test Kwargs.run returns correct tuple structure."""
    obj = target.Kwargs()
    result = obj.run(positional, named=named, **kwargs)
    
    assert len(result) == 3
    assert result[0] == positional
    assert result[1] == named
    assert result[2] == kwargs


@given(
    alpha=st.integers(min_value=-1000, max_value=1000),
    beta=st.integers(min_value=-1000, max_value=1000)
)
def test_mixed_defaults_sum(alpha, beta):
    """Test MixedDefaults.sum calculation."""
    obj = target.MixedDefaults()
    result = obj.sum(alpha, beta)
    
    # According to the implementation: alpha + 2 * beta
    assert result == alpha + 2 * beta
    
    # Test with defaults
    assert obj.sum() == 0 + 2 * 0
    assert obj.sum(alpha=5) == 5 + 2 * 0
    assert obj.sum(beta=3) == 0 + 2 * 3


def test_mixed_defaults_ten():
    """Test MixedDefaults.ten always returns 10."""
    obj = target.MixedDefaults()
    assert obj.ten() == 10


@given(
    alpha=st.one_of(st.integers(), st.text()),
    beta=st.text()
)
def test_mixed_defaults_identity(alpha, beta):
    """Test MixedDefaults.identity returns both arguments."""
    obj = target.MixedDefaults()
    result = obj.identity(alpha, beta)
    
    assert result == (alpha, beta)
    
    # Test with default beta
    result_default = obj.identity(alpha)
    assert result_default == (alpha, '0')


@given(count=st.integers(min_value=-10000, max_value=10000))
def test_with_defaults_double(count):
    """Test WithDefaults.double multiplies by 2."""
    obj = target.WithDefaults()
    result = obj.double(count)
    assert result == 2 * count
    
    # Test default
    assert obj.double() == 0


@given(count=st.integers(min_value=-10000, max_value=10000))
def test_with_defaults_triple(count):
    """Test WithDefaults.triple multiplies by 3."""
    obj = target.WithDefaults()
    result = obj.triple(count)
    assert result == 3 * count
    
    # Test default
    assert obj.triple() == 0


@given(string=st.text())
def test_with_defaults_text(string):
    """Test WithDefaults.text returns the input string."""
    obj = target.WithDefaults()
    result = obj.text(string)
    assert result == string
    
    # Test default (long string of digits)
    default_result = obj.text()
    assert default_result == ('0001020304050607080910111213141516171819'
                              '2021222324252627282930313233343536373839')


@given(number=st.integers())
def test_invalid_property_double(number):
    """Test InvalidProperty.double method works correctly."""
    obj = target.InvalidProperty()
    result = obj.double(number)
    assert result == 2 * number


def test_invalid_property_prop_raises():
    """Test that InvalidProperty.prop raises ValueError."""
    obj = target.InvalidProperty()
    try:
        _ = obj.prop
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert str(e) == 'test'


# Test for potential edge cases and bugs

@given(
    size=st.integers(min_value=-10, max_value=0)
)
def test_binary_canvas_negative_size(size):
    """Test BinaryCanvas with negative or zero size."""
    try:
        canvas = target.BinaryCanvas(size=size)
        # If it accepts negative/zero size, test the behavior
        if size <= 0:
            # This might be a bug - canvas with non-positive size
            assert len(canvas.pixels) == size
    except (ValueError, IndexError):
        pass  # Expected for invalid sizes


@given(
    x=st.floats(allow_nan=True, allow_infinity=True),
    y=st.floats(allow_nan=True, allow_infinity=True)
)
def test_subpoint_with_special_floats(x, y):
    """Test SubPoint with NaN and infinity values."""
    try:
        point = target.SubPoint(x, y)
        result = point.coordinate_sum()
        
        # Check for special float handling
        if math.isnan(x) or math.isnan(y):
            assert math.isnan(result)
        elif math.isinf(x) or math.isinf(y):
            # inf + finite = inf, inf + inf = inf, inf + -inf = nan
            if math.isinf(x) and math.isinf(y) and (x > 0) != (y > 0):
                assert math.isnan(result)
            else:
                assert math.isinf(result) or math.isnan(result)
    except TypeError:
        # NamedTuple might not accept floats
        pass