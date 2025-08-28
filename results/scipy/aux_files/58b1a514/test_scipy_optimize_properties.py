"""Property-based tests for scipy.optimize using Hypothesis."""

import math
import numpy as np
from hypothesis import given, assume, strategies as st, settings
import scipy.optimize as opt
import pytest


# Strategy for well-behaved polynomial coefficients
polynomial_coeffs = st.lists(
    st.floats(min_value=-10, max_value=10, allow_nan=False, allow_infinity=False),
    min_size=2,
    max_size=5
)

# Strategy for safe floating point values
safe_floats = st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False)
positive_floats = st.floats(min_value=0.1, max_value=100, allow_nan=False, allow_infinity=False)
small_positive_floats = st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False)


@given(
    coeffs=polynomial_coeffs,
    a=safe_floats,
    b=safe_floats
)
@settings(max_examples=100)
def test_root_finding_consistency(coeffs, a, b):
    """Test that bisect, brentq, and brenth find the same root for polynomials."""
    # Create a polynomial function
    def f(x):
        return sum(c * x**i for i, c in enumerate(coeffs))
    
    # Ensure we have a valid bracket
    assume(a < b)
    fa, fb = f(a), f(b)
    assume(not math.isnan(fa) and not math.isnan(fb))
    assume(not math.isinf(fa) and not math.isinf(fb))
    assume(fa * fb < 0)  # Opposite signs required
    
    # Find roots using different methods
    try:
        root_bisect = opt.bisect(f, a, b, xtol=1e-10)
        root_brentq = opt.brentq(f, a, b, xtol=1e-10)
        root_brenth = opt.brenth(f, a, b, xtol=1e-10)
        
        # All methods should find approximately the same root
        assert math.isclose(root_bisect, root_brentq, rel_tol=1e-8, abs_tol=1e-10)
        assert math.isclose(root_bisect, root_brenth, rel_tol=1e-8, abs_tol=1e-10)
        
        # The root should actually be a root
        assert abs(f(root_bisect)) < 1e-8
        assert abs(f(root_brentq)) < 1e-8
        assert abs(f(root_brenth)) < 1e-8
        
        # Root should be within the bracket
        assert min(a, b) <= root_bisect <= max(a, b)
        assert min(a, b) <= root_brentq <= max(a, b)
        assert min(a, b) <= root_brenth <= max(a, b)
        
    except (ValueError, RuntimeError):
        # Some functions may not converge, that's acceptable
        pass


@given(
    x=st.lists(safe_floats, min_size=1, max_size=5),
    epsilon=st.floats(min_value=1e-10, max_value=1e-5, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100)
def test_approx_fprime_polynomial(x, epsilon):
    """Test that approx_fprime correctly approximates gradients of polynomials."""
    x = np.array(x)
    
    # Define a simple quadratic function with known gradient
    def f(x):
        return np.sum(x**2)
    
    def true_grad(x):
        return 2 * x
    
    # Compute approximate gradient
    approx_grad = opt.approx_fprime(x, f, epsilon)
    true_gradient = true_grad(x)
    
    # The approximation should be close to the true gradient
    # Tolerance depends on epsilon
    tol = max(epsilon * 100, 1e-6)
    assert np.allclose(approx_grad, true_gradient, rtol=tol, atol=tol)


@given(
    x=st.lists(safe_floats, min_size=1, max_size=5),
    epsilon=st.floats(min_value=1e-10, max_value=1e-5, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100) 
def test_check_grad_consistency(x, epsilon):
    """Test that check_grad is consistent with approx_fprime."""
    x = np.array(x)
    
    # Define a function and its gradient
    def f(x):
        return np.sum(x**3) + np.sum(x**2)
    
    def grad_f(x):
        return 3 * x**2 + 2 * x
    
    # check_grad should return a small value for correct gradient
    error = opt.check_grad(f, grad_f, x, epsilon=epsilon)
    
    # The error should be small (proportional to epsilon)
    assert error < epsilon * 1000
    
    # Also verify that approx_fprime gives similar results
    approx = opt.approx_fprime(x, f, epsilon)
    true_grad = grad_f(x)
    assert np.allclose(approx, true_grad, rtol=epsilon*100, atol=epsilon*100)


@given(
    coeffs=st.lists(
        st.floats(min_value=-5, max_value=5, allow_nan=False, allow_infinity=False),
        min_size=3,
        max_size=4
    ),
    x0=safe_floats
)
@settings(max_examples=100)
def test_newton_convergence(coeffs, x0):
    """Test Newton's method with explicit derivative."""
    # Create polynomial and its derivative
    def f(x):
        return sum(c * x**i for i, c in enumerate(coeffs))
    
    def fprime(x):
        return sum(i * c * x**(i-1) for i, c in enumerate(coeffs) if i > 0)
    
    # Skip if derivative is too small at x0
    fp = fprime(x0)
    assume(abs(fp) > 1e-10)
    
    try:
        # Newton with derivative should converge
        root = opt.newton(f, x0, fprime=fprime, maxiter=100, tol=1e-10)
        
        # Verify it's actually a root
        assert abs(f(root)) < 1e-6
        
    except (RuntimeError, ValueError):
        # Newton's method may not converge for all starting points
        pass


@given(
    a=safe_floats,
    b=safe_floats,
    c=safe_floats,
    bracket_start=st.floats(min_value=-10, max_value=10, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100)
def test_minimize_scalar_quadratic(a, b, c, bracket_start):
    """Test minimize_scalar on quadratic functions."""
    # Make it a proper minimum (positive curvature)
    assume(a > 0.1)
    
    # Define quadratic with known minimum
    def f(x):
        return a * x**2 + b * x + c
    
    # Analytical minimum is at x = -b/(2a)
    true_min_x = -b / (2 * a)
    true_min_val = f(true_min_x)
    
    # Find minimum using minimize_scalar
    result = opt.minimize_scalar(f, bracket=(bracket_start-5, bracket_start, bracket_start+5))
    
    # Should find the true minimum
    assert math.isclose(result.x, true_min_x, rel_tol=1e-5, abs_tol=1e-5)
    assert math.isclose(result.fun, true_min_val, rel_tol=1e-5, abs_tol=1e-5)
    
    # Also test with golden method
    result_golden = opt.golden(f, brack=(bracket_start-5, bracket_start, bracket_start+5))
    assert math.isclose(result_golden, true_min_x, rel_tol=1e-3, abs_tol=1e-3)


@given(
    x=st.lists(
        st.floats(min_value=-10, max_value=10, allow_nan=False, allow_infinity=False),
        min_size=2,
        max_size=5
    )
)
@settings(max_examples=100)
def test_approx_fprime_vector_function(x):
    """Test approx_fprime with vector-valued functions."""
    x = np.array(x)
    
    # Define a vector-valued function (returns multiple outputs)
    def f(x):
        return np.array([np.sum(x**2), np.sum(x**3), np.prod(x)])
    
    # For scalar functions called multiple times
    def f0(x):
        return np.sum(x**2)
    
    def f1(x):
        return np.sum(x**3)
    
    # Approximate gradients
    grad0 = opt.approx_fprime(x, f0)
    grad1 = opt.approx_fprime(x, f1)
    
    # Known analytical gradients
    true_grad0 = 2 * x
    true_grad1 = 3 * x**2
    
    # Check approximations
    assert np.allclose(grad0, true_grad0, rtol=1e-5, atol=1e-7)
    assert np.allclose(grad1, true_grad1, rtol=1e-5, atol=1e-7)


@given(
    x0=st.floats(min_value=0.1, max_value=10, allow_nan=False, allow_infinity=False),
    fprime2_provided=st.booleans()
)
@settings(max_examples=50)
def test_newton_with_second_derivative(x0, fprime2_provided):
    """Test Newton's method with and without second derivative (Halley's method)."""
    # Use exponential function with known derivatives
    def f(x):
        return np.exp(x) - 2*x - 1
    
    def fprime(x):
        return np.exp(x) - 2
    
    def fprime2(x):
        return np.exp(x)
    
    try:
        if fprime2_provided:
            # Halley's method
            root = opt.newton(f, x0, fprime=fprime, fprime2=fprime2, maxiter=50)
        else:
            # Standard Newton
            root = opt.newton(f, x0, fprime=fprime, maxiter=50)
        
        # Should find a root
        assert abs(f(root)) < 1e-8
        
    except (RuntimeError, ValueError):
        # May not converge for all starting points
        pass