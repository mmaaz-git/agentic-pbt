import numpy as np
import pytest
from hypothesis import assume, given, strategies as st, settings
from scipy import interpolate


# Strategy for generating valid x points (strictly increasing)
@st.composite
def strictly_increasing_array(draw, min_size=2, max_size=10):
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    deltas = draw(st.lists(
        st.floats(min_value=0.01, max_value=10, allow_nan=False, allow_infinity=False),
        min_size=size, max_size=size
    ))
    x = np.cumsum([0] + deltas[:-1])
    return x


# Strategy for generating y values
def y_values_strategy(size):
    return st.lists(
        st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
        min_size=size, max_size=size
    )


# Test 1: All interpolators should pass through given points
@given(
    x=strictly_increasing_array(min_size=3, max_size=20),
    y_gen=st.data()
)
@settings(max_examples=200)
def test_interpolation_passes_through_points(x, y_gen):
    y = np.array(y_gen.draw(y_values_strategy(len(x))))
    
    # Test various interpolators
    interpolators = [
        interpolate.CubicSpline(x, y),
        interpolate.PchipInterpolator(x, y),
        interpolate.BarycentricInterpolator(x, y),
        interpolate.KroghInterpolator(x, y),
        interpolate.interp1d(x, y, kind='linear'),
    ]
    
    for interp in interpolators:
        result = interp(x)
        assert np.allclose(result, y, rtol=1e-10, atol=1e-10), \
            f"{interp.__class__.__name__} doesn't pass through points"


# Test 2: PchipInterpolator should preserve monotonicity
@given(
    x=strictly_increasing_array(min_size=3, max_size=15),
    increasing=st.booleans()
)
@settings(max_examples=100)
def test_pchip_monotonicity_preservation(x, increasing):
    # Generate monotonic y values
    if increasing:
        y = np.sort(np.random.randn(len(x)))
    else:
        y = np.sort(np.random.randn(len(x)))[::-1]
    
    pchip = interpolate.PchipInterpolator(x, y)
    
    # Test monotonicity on dense grid
    x_test = np.linspace(x[0], x[-1], 100)
    y_test = pchip(x_test)
    
    # Check monotonicity is preserved
    diffs = np.diff(y_test)
    if increasing:
        assert np.all(diffs >= -1e-10), "PCHIP didn't preserve increasing monotonicity"
    else:
        assert np.all(diffs <= 1e-10), "PCHIP didn't preserve decreasing monotonicity"


# Test 3: CubicSpline with periodic boundary conditions
@given(
    x=strictly_increasing_array(min_size=4, max_size=15),
    y_gen=st.data()
)
@settings(max_examples=100)  
def test_cubic_spline_periodic_boundary(x, y_gen):
    # For periodic BC, first and last y must be equal
    y_middle = y_gen.draw(y_values_strategy(len(x) - 1))
    y = np.array(y_middle + [y_middle[0]])  # Make periodic
    
    try:
        cs = interpolate.CubicSpline(x, y, bc_type='periodic')
    except ValueError as e:
        # Skip if scipy rejects our input
        assume(False)
        return
    
    # Test that derivatives match at boundaries
    derivative = cs.derivative()
    d_start = derivative(x[0])
    d_end = derivative(x[-1])
    
    # For periodic splines, derivatives should match at boundaries
    assert np.allclose(d_start, d_end, rtol=1e-8, atol=1e-8), \
        "Periodic CubicSpline derivatives don't match at boundaries"
    
    # Second derivatives should also match
    second_deriv = derivative.derivative()
    d2_start = second_deriv(x[0]) 
    d2_end = second_deriv(x[-1])
    
    assert np.allclose(d2_start, d2_end, rtol=1e-8, atol=1e-8), \
        "Periodic CubicSpline second derivatives don't match at boundaries"


# Test 4: CubicSpline should be C2 continuous (smooth second derivative)
@given(
    x=strictly_increasing_array(min_size=4, max_size=10),
    y_gen=st.data()
)
@settings(max_examples=100)
def test_cubic_spline_c2_continuity(x, y_gen):
    y = np.array(y_gen.draw(y_values_strategy(len(x))))
    
    cs = interpolate.CubicSpline(x, y)
    
    # Check continuity at interior knots
    for i in range(1, len(x) - 1):
        knot = x[i]
        eps = 1e-10
        
        # Check second derivative continuity
        second_deriv = cs.derivative(2)
        left = second_deriv(knot - eps)
        right = second_deriv(knot + eps)
        
        assert np.allclose(left, right, rtol=1e-6, atol=1e-6), \
            f"CubicSpline second derivative not continuous at knot {knot}"


# Test 5: BarycentricInterpolator update functionality
@given(
    x=strictly_increasing_array(min_size=3, max_size=10),
    y1_gen=st.data(),
    y2_gen=st.data()
)
@settings(max_examples=100)
def test_barycentric_update_property(x, y1_gen, y2_gen):
    y1 = np.array(y1_gen.draw(y_values_strategy(len(x))))
    y2 = np.array(y2_gen.draw(y_values_strategy(len(x))))
    
    # Create interpolator with first set
    bi = interpolate.BarycentricInterpolator(x, y1)
    
    # Update with new y values
    bi.set_yi(y2)
    
    # Should now interpolate the new values
    result = bi(x)
    assert np.allclose(result, y2, rtol=1e-10, atol=1e-10), \
        "BarycentricInterpolator update didn't work correctly"


# Test 6: Akima1DInterpolator edge case with few points
@given(
    x=strictly_increasing_array(min_size=2, max_size=5),
    y_gen=st.data()
)
@settings(max_examples=100)
def test_akima_small_dataset(x, y_gen):
    y = np.array(y_gen.draw(y_values_strategy(len(x))))
    
    # Akima needs at least 2 points
    if len(x) < 2:
        return
        
    akima = interpolate.Akima1DInterpolator(x, y)
    
    # Should still pass through points
    result = akima(x)
    assert np.allclose(result, y, rtol=1e-10, atol=1e-10), \
        "Akima1DInterpolator doesn't pass through points with small dataset"


# Test 7: UnivariateSpline with smoothing factor
@given(
    x=strictly_increasing_array(min_size=4, max_size=20),
    y_gen=st.data(),
    s=st.floats(min_value=0, max_value=100, allow_nan=False)
)
@settings(max_examples=50)
def test_univariate_spline_smoothing(x, y_gen, s):
    y = np.array(y_gen.draw(y_values_strategy(len(x))))
    
    # Create spline with smoothing
    try:
        spline = interpolate.UnivariateSpline(x, y, s=s)
    except:
        # Some combinations might fail
        assume(False)
        return
    
    # With s=0, should pass through points exactly
    if s == 0:
        result = spline(x)
        assert np.allclose(result, y, rtol=1e-6, atol=1e-6), \
            "UnivariateSpline with s=0 doesn't pass through points"


# Test 8: LinearNDInterpolator basic properties
@given(
    n_points=st.integers(min_value=4, max_value=20),
    data_gen=st.data()
)
@settings(max_examples=50)
def test_linear_nd_interpolator_2d(n_points, data_gen):
    # Generate random 2D points
    points = data_gen.draw(st.lists(
        st.tuples(
            st.floats(min_value=-10, max_value=10, allow_nan=False),
            st.floats(min_value=-10, max_value=10, allow_nan=False)
        ),
        min_size=n_points, max_size=n_points, unique=True
    ))
    points = np.array(points)
    
    values = data_gen.draw(st.lists(
        st.floats(min_value=-100, max_value=100, allow_nan=False),
        min_size=n_points, max_size=n_points
    ))
    
    # Create interpolator
    interp = interpolate.LinearNDInterpolator(points, values)
    
    # Should pass through given points
    result = interp(points)
    valid_mask = ~np.isnan(result)
    
    assert np.allclose(result[valid_mask], np.array(values)[valid_mask], rtol=1e-10, atol=1e-10), \
        "LinearNDInterpolator doesn't pass through points"


# Test 9: RBFInterpolator basic properties  
@given(
    n_points=st.integers(min_value=3, max_value=10),
    data_gen=st.data()
)
@settings(max_examples=30)
def test_rbf_interpolator(n_points, data_gen):
    # Generate random 2D points
    points = data_gen.draw(st.lists(
        st.tuples(
            st.floats(min_value=-5, max_value=5, allow_nan=False),
            st.floats(min_value=-5, max_value=5, allow_nan=False)
        ),
        min_size=n_points, max_size=n_points, unique=True
    ))
    points = np.array(points)
    
    values = data_gen.draw(st.lists(
        st.floats(min_value=-10, max_value=10, allow_nan=False),
        min_size=n_points, max_size=n_points
    ))
    values = np.array(values)
    
    try:
        # Create RBF interpolator
        rbf = interpolate.RBFInterpolator(points, values.reshape(-1, 1))
        
        # Should approximately pass through given points
        result = rbf(points).flatten()
        
        assert np.allclose(result, values, rtol=1e-5, atol=1e-5), \
            "RBFInterpolator doesn't pass through points accurately"
    except np.linalg.LinAlgError:
        # Sometimes the system is ill-conditioned
        assume(False)


# Test 10: Make sure interpolators handle edge case inputs correctly
@given(
    x_base=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    y_base=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100)
def test_two_point_interpolation(x_base, y_base):
    # Minimal case: just two points
    x = np.array([x_base, x_base + 1.0])
    y = np.array([y_base, y_base + 2.0])
    
    # These should all handle two points
    interpolators = [
        interpolate.interp1d(x, y, kind='linear'),
        interpolate.BarycentricInterpolator(x, y),
        interpolate.KroghInterpolator(x, y),
    ]
    
    for interp in interpolators:
        result = interp(x)
        assert np.allclose(result, y, rtol=1e-10, atol=1e-10), \
            f"{interp.__class__.__name__} fails with two points"


# Test 11: Specific test for extrapolation behavior
@given(
    x=strictly_increasing_array(min_size=3, max_size=10),
    y_gen=st.data(),
    test_point=st.floats(min_value=-100, max_value=100, allow_nan=False)
)
@settings(max_examples=50)
def test_extrapolation_behavior(x, y_gen, test_point):
    y = np.array(y_gen.draw(y_values_strategy(len(x))))
    
    # CubicSpline with extrapolate=True
    cs_extrap = interpolate.CubicSpline(x, y, extrapolate=True)
    
    # Should not raise error for any point
    result = cs_extrap(test_point)
    assert np.isfinite(result), "CubicSpline extrapolation gave non-finite result"
    
    # CubicSpline with extrapolate=False
    cs_no_extrap = interpolate.CubicSpline(x, y, extrapolate=False)
    
    # Should give NaN outside range
    if test_point < x[0] or test_point > x[-1]:
        result = cs_no_extrap(test_point)
        assert np.isnan(result), "CubicSpline with extrapolate=False didn't return NaN"