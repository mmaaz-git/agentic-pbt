"""Property-based tests for scipy.differentiate module."""

import numpy as np
import pytest
from hypothesis import given, strategies as st, assume, settings
from scipy import differentiate
import math


# Strategy for reasonable floating point values
reasonable_floats = st.floats(
    min_value=-100, 
    max_value=100, 
    allow_nan=False, 
    allow_infinity=False,
    allow_subnormal=False
)

# Strategy for small positive floats (for step sizes)
small_positive_floats = st.floats(
    min_value=1e-8,
    max_value=1.0,
    allow_nan=False,
    allow_infinity=False
)


class TestHessianSymmetry:
    """Test that Hessian matrices are symmetric for smooth functions."""
    
    @given(
        x0=reasonable_floats,
        x1=reasonable_floats,
        a=reasonable_floats,
        b=reasonable_floats,
        c=reasonable_floats
    )
    @settings(max_examples=100)
    def test_hessian_symmetry_quadratic(self, x0, x1, a, b, c):
        """Test Hessian symmetry for a quadratic function."""
        # Use a simple quadratic function: f(x) = a*x[0]^2 + b*x[1]^2 + c*x[0]*x[1]
        def f(x):
            return a * x[0]**2 + b * x[1]**2 + c * x[0] * x[1]
        
        x = np.array([x0, x1])
        
        # Skip if x values are too large (can cause numerical issues)
        assume(np.all(np.abs(x) < 50))
        
        res = differentiate.hessian(f, x, tolerances={'atol': 1e-6, 'rtol': 1e-6})
        
        # Check that the Hessian is symmetric
        H = res.df
        
        # The Hessian should be symmetric: H[i,j] = H[j,i]
        # Using a reasonable tolerance for floating point comparison
        assert np.allclose(H, H.T, rtol=1e-5, atol=1e-8), \
            f"Hessian not symmetric: max diff = {np.max(np.abs(H - H.T))}"
    
    @given(
        x=st.lists(reasonable_floats, min_size=2, max_size=4),
        coeffs=st.lists(reasonable_floats, min_size=3, max_size=10)
    )
    @settings(max_examples=50)
    def test_hessian_symmetry_polynomial(self, x, coeffs):
        """Test Hessian symmetry for polynomial functions."""
        x = np.array(x)
        assume(np.all(np.abs(x) < 20))
        
        # Create a polynomial function
        def f(x):
            result = coeffs[0]
            if len(coeffs) > 1 and len(x) > 0:
                result += coeffs[1] * x[0]
            if len(coeffs) > 2 and len(x) > 1:
                result += coeffs[2] * x[1]
            # Add some cross terms to make it interesting
            if len(coeffs) > 3 and len(x) > 1:
                result += coeffs[3] * x[0] * x[1]
            if len(coeffs) > 4 and len(x) > 0:
                result += coeffs[4] * x[0]**2
            if len(coeffs) > 5 and len(x) > 1:
                result += coeffs[5] * x[1]**2
            return result
        
        res = differentiate.hessian(f, x, tolerances={'atol': 1e-6, 'rtol': 1e-6})
        H = res.df
        
        # Check symmetry
        assert np.allclose(H, H.T, rtol=1e-4, atol=1e-7), \
            f"Hessian not symmetric for polynomial: max diff = {np.max(np.abs(H - H.T))}"


class TestJacobianDerivativeConsistency:
    """Test that Jacobian and derivative give consistent results for scalar functions."""
    
    @given(
        x=reasonable_floats,
        power=st.floats(min_value=1.0, max_value=5.0)
    )
    @settings(max_examples=100)
    def test_scalar_consistency_power(self, x, power):
        """Test jacobian/derivative consistency for power functions."""
        assume(abs(x) > 0.01)  # Avoid near-zero where derivatives can be tricky
        assume(abs(x) < 50)
        
        def f(x):
            return x ** power
        
        # For scalar function, derivative and jacobian should give same result
        der_res = differentiate.derivative(f, x, tolerances={'atol': 1e-8, 'rtol': 1e-8})
        
        # Jacobian expects array input/output
        def f_array(x_arr):
            return np.array([x_arr[0] ** power])
        
        jac_res = differentiate.jacobian(f_array, np.array([x]), 
                                        tolerances={'atol': 1e-8, 'rtol': 1e-8})
        
        # The Jacobian should be a 1x1 matrix with the same value as derivative
        assert jac_res.df.shape == (1, 1), f"Expected shape (1,1), got {jac_res.df.shape}"
        
        # Check they are close
        assert np.allclose(der_res.df, jac_res.df[0, 0], rtol=1e-6, atol=1e-9), \
            f"Derivative {der_res.df} != Jacobian {jac_res.df[0, 0]}"
    
    @given(x=reasonable_floats)
    @settings(max_examples=100) 
    def test_scalar_consistency_trig(self, x):
        """Test consistency for trigonometric functions."""
        assume(abs(x) < 10)  # Keep in reasonable range for trig functions
        
        # Test with sine function
        def f_scalar(x):
            return np.sin(x)
        
        def f_array(x_arr):
            return np.array([np.sin(x_arr[0])])
        
        der_res = differentiate.derivative(f_scalar, x, tolerances={'atol': 1e-8, 'rtol': 1e-8})
        jac_res = differentiate.jacobian(f_array, np.array([x]), 
                                        tolerances={'atol': 1e-8, 'rtol': 1e-8})
        
        assert np.allclose(der_res.df, jac_res.df[0, 0], rtol=1e-6, atol=1e-9), \
            f"sin: Derivative {der_res.df} != Jacobian {jac_res.df[0, 0]}"


class TestNumericalStability:
    """Test that functions don't crash on valid inputs."""
    
    @given(
        x=st.lists(reasonable_floats, min_size=1, max_size=5),
        initial_step=small_positive_floats,
        order=st.integers(min_value=2, max_value=8).map(lambda x: 2 * (x // 2)),  # Even integers
        maxiter=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=200)
    def test_derivative_no_crash(self, x, initial_step, order, maxiter):
        """Test that derivative doesn't crash on various inputs."""
        x = np.array(x)
        assume(np.all(np.abs(x) < 50))
        
        def f(x):
            # A simple smooth function that should work everywhere
            return np.sum(x**2) + np.sum(np.sin(x))
        
        # This should not raise an exception
        try:
            res = differentiate.derivative(f, x[0] if len(x) == 1 else x, 
                                          initial_step=initial_step,
                                          order=order,
                                          maxiter=maxiter)
            # Result should be finite
            assert np.all(np.isfinite(res.df) | (res.status != 0)), \
                "Got non-finite result with successful status"
        except Exception as e:
            pytest.fail(f"derivative raised unexpected exception: {e}")
    
    @given(
        x=st.lists(reasonable_floats, min_size=2, max_size=3),
        initial_step=small_positive_floats
    )
    @settings(max_examples=100)
    def test_jacobian_no_crash(self, x, initial_step):
        """Test that jacobian doesn't crash on various inputs."""
        x = np.array(x)
        assume(np.all(np.abs(x) < 30))
        
        n = len(x)
        
        def f(x):
            # Return a vector output
            return np.array([np.sum(x**2), np.sum(np.sin(x))])
        
        try:
            res = differentiate.jacobian(f, x, initial_step=initial_step,
                                        tolerances={'atol': 1e-6, 'rtol': 1e-6})
            # Check shape is correct
            assert res.df.shape == (2, n), f"Expected shape (2, {n}), got {res.df.shape}"
        except Exception as e:
            pytest.fail(f"jacobian raised unexpected exception: {e}")
    
    @given(
        x=st.lists(reasonable_floats, min_size=2, max_size=3),
        initial_step=small_positive_floats
    )
    @settings(max_examples=100)
    def test_hessian_no_crash(self, x, initial_step):
        """Test that hessian doesn't crash on various inputs."""
        x = np.array(x)
        assume(np.all(np.abs(x) < 30))
        
        def f(x):
            return np.sum(x**2) + np.prod(np.sin(x))
        
        try:
            res = differentiate.hessian(f, x, initial_step=initial_step,
                                       tolerances={'atol': 1e-6, 'rtol': 1e-6})
            # Check shape and symmetry
            n = len(x)
            assert res.df.shape == (n, n), f"Expected shape ({n}, {n}), got {res.df.shape}"
        except Exception as e:
            pytest.fail(f"hessian raised unexpected exception: {e}")


class TestConvergenceProperty:
    """Test that error decreases with iterations for smooth functions."""
    
    @given(
        x=reasonable_floats,
        initial_step=st.floats(min_value=0.01, max_value=0.5)
    )
    @settings(max_examples=50)
    def test_convergence_smooth_function(self, x, initial_step):
        """Test that error decreases for smooth functions."""
        assume(abs(x) < 20)
        assume(abs(x) > 0.1)  # Avoid near zero
        
        def f(x):
            return np.exp(x)  # Smooth function with known derivative
        
        true_derivative = np.exp(x)
        
        errors = []
        for maxiter in [1, 2, 3, 4]:
            res = differentiate.derivative(f, x, 
                                          initial_step=initial_step,
                                          maxiter=maxiter,
                                          tolerances={'atol': 0, 'rtol': 0})  # Don't stop early
            error = abs(res.df - true_derivative)
            errors.append(error)
        
        # Errors should generally decrease (allowing for some numerical noise)
        # Check that at least one later iteration is better than the first
        assert any(errors[i] < errors[0] * 0.9 for i in range(1, len(errors))), \
            f"Errors did not decrease: {errors}"


class TestStepDirectionConsistency:
    """Test consistency of results with different step directions."""
    
    @given(
        x=reasonable_floats,
        initial_step=small_positive_floats
    )
    @settings(max_examples=100)
    def test_step_direction_opposite(self, x, initial_step):
        """Test that opposite step directions give consistent results for smooth functions."""
        assume(abs(x) > 1.0)  # Avoid boundary issues
        assume(abs(x) < 20)
        
        def f(x):
            # Smooth function defined everywhere
            return x**3 + np.sin(x)
        
        # Compare left-sided and right-sided differences
        res_left = differentiate.derivative(f, x, 
                                           step_direction=-1,
                                           initial_step=initial_step,
                                           tolerances={'atol': 1e-6, 'rtol': 1e-6})
        
        res_right = differentiate.derivative(f, x,
                                            step_direction=1, 
                                            initial_step=initial_step,
                                            tolerances={'atol': 1e-6, 'rtol': 1e-6})
        
        # For smooth functions, left and right derivatives should be very close
        # Using a slightly relaxed tolerance since one-sided differences are less accurate
        assert np.allclose(res_left.df, res_right.df, rtol=1e-3, atol=1e-5), \
            f"Left derivative {res_left.df} != Right derivative {res_right.df}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])