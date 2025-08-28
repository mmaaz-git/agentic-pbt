import numpy as np
import scipy.integrate as integrate
from hypothesis import given, strategies as st, assume, settings
import math


# Strategy for generating valid x arrays (sorted, no duplicates)
@st.composite
def x_arrays(draw, min_size=3, max_size=20):
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    # Generate unique values and sort them
    values = draw(st.lists(
        st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
        min_size=size, max_size=size, unique=True
    ))
    return np.array(sorted(values))


# Strategy for y arrays given an x array
def y_arrays(x_size):
    return st.lists(
        st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
        min_size=x_size, max_size=x_size
    ).map(np.array)


# Test 1: Cumulative consistency - last element should match total integral
@given(x=x_arrays(), y=st.data())
@settings(max_examples=1000)
def test_cumulative_consistency_trapezoid(x, y):
    y_vals = y.draw(y_arrays(len(x)))
    
    total = integrate.trapezoid(y_vals, x)
    cumulative = integrate.cumulative_trapezoid(y_vals, x, initial=0)
    
    assert math.isclose(total, cumulative[-1], rel_tol=1e-10, abs_tol=1e-10), \
        f"Trapezoid: total={total}, cumulative[-1]={cumulative[-1]}"


@given(x=x_arrays(), y=st.data())
@settings(max_examples=1000)
def test_cumulative_consistency_simpson(x, y):
    y_vals = y.draw(y_arrays(len(x)))
    
    total = integrate.simpson(y_vals, x)
    cumulative = integrate.cumulative_simpson(y_vals, x=x, initial=0)
    
    assert math.isclose(total, cumulative[-1], rel_tol=1e-10, abs_tol=1e-10), \
        f"Simpson: total={total}, cumulative[-1]={cumulative[-1]}"


# Test 2: Monotonicity for non-negative functions
@given(x=x_arrays(min_size=4))
@settings(max_examples=500)
def test_cumulative_monotonicity_nonnegative(x):
    # Use non-negative y values
    y = np.abs(np.random.randn(len(x)))
    
    cum_trap = integrate.cumulative_trapezoid(y, x, initial=0)
    cum_simp = integrate.cumulative_simpson(y, x=x, initial=0)
    
    # Check monotonic increasing
    assert all(cum_trap[i] <= cum_trap[i+1] for i in range(len(cum_trap)-1)), \
        f"Trapezoid cumulative not monotonic for non-negative function"
    assert all(cum_simp[i] <= cum_simp[i+1] for i in range(len(cum_simp)-1)), \
        f"Simpson cumulative not monotonic for non-negative function"


# Test 3: Linearity - integrate(c*f) = c * integrate(f)
@given(x=x_arrays(), y=st.data(), c=st.floats(min_value=-10, max_value=10, allow_nan=False))
@settings(max_examples=500)
def test_linearity_trapezoid(x, y, c):
    assume(abs(c) > 1e-10)  # Avoid near-zero scaling
    y_vals = y.draw(y_arrays(len(x)))
    
    integral_y = integrate.trapezoid(y_vals, x)
    integral_cy = integrate.trapezoid(c * y_vals, x)
    
    assert math.isclose(c * integral_y, integral_cy, rel_tol=1e-10, abs_tol=1e-10), \
        f"Linearity failed: c*integrate(y)={c * integral_y}, integrate(c*y)={integral_cy}"


@given(x=x_arrays(), y=st.data(), c=st.floats(min_value=-10, max_value=10, allow_nan=False))
@settings(max_examples=500)
def test_linearity_simpson(x, y, c):
    assume(abs(c) > 1e-10)  # Avoid near-zero scaling
    y_vals = y.draw(y_arrays(len(x)))
    
    integral_y = integrate.simpson(y_vals, x)
    integral_cy = integrate.simpson(c * y_vals, x)
    
    assert math.isclose(c * integral_y, integral_cy, rel_tol=1e-10, abs_tol=1e-10), \
        f"Linearity failed: c*integrate(y)={c * integral_y}, integrate(c*y)={integral_cy}"


# Test 4: Edge case - very close x values
@given(
    base_x=st.lists(
        st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
        min_size=5, max_size=10, unique=True
    ),
    epsilon=st.floats(min_value=1e-10, max_value=1e-5)
)
@settings(max_examples=500)
def test_simpson_close_x_values(base_x, epsilon):
    # Create x array with some very close values
    x = sorted(base_x)
    # Insert a close value
    if len(x) > 2:
        insert_idx = len(x) // 2
        x.insert(insert_idx + 1, x[insert_idx] + epsilon)
    
    x = np.array(x)
    y = np.random.randn(len(x))
    
    # Simpson should not blow up with close x values
    result = integrate.simpson(y, x)
    
    # Check result is reasonable (not huge)
    assert abs(result) < 1e6, f"Simpson gave unreasonable result {result} with close x values"
    
    # Compare with trapezoid - they should be in the same ballpark
    trap_result = integrate.trapezoid(y, x)
    
    # They don't need to be exactly equal, but should be same order of magnitude
    if abs(trap_result) > 1e-10:
        ratio = abs(result / trap_result)
        assert 0.01 < ratio < 100, \
            f"Simpson ({result}) vastly different from trapezoid ({trap_result}) with close x values"


# Test 5: Non-uniform spacing behavior
@given(
    x_uniform=x_arrays(min_size=5, max_size=15),
    y=st.data()
)
@settings(max_examples=500)
def test_simpson_nonuniform_spacing(x_uniform, y):
    # Create non-uniform spacing by perturbing uniform spacing
    x = x_uniform.copy()
    # Perturb middle values slightly
    for i in range(1, len(x)-1):
        if i % 2 == 0:
            x[i] += (x[i+1] - x[i]) * 0.1  # Move slightly right
    
    y_vals = y.draw(y_arrays(len(x)))
    
    simpson_result = integrate.simpson(y_vals, x)
    trapezoid_result = integrate.trapezoid(y_vals, x)
    
    # For reasonable functions, simpson and trapezoid should give similar results
    # If they differ by orders of magnitude, something is wrong
    if abs(trapezoid_result) > 1e-10:
        ratio = abs(simpson_result / trapezoid_result)
        assert 0.001 < ratio < 1000, \
            f"Simpson ({simpson_result}) wildly different from trapezoid ({trapezoid_result}) for non-uniform spacing"