"""Property-based tests for scipy.odr module"""

import numpy as np
import scipy.odr as odr
from hypothesis import given, strategies as st, assume, settings
import math


# Strategies for generating valid inputs
valid_floats = st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6)
small_floats = st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)
positive_floats = st.floats(min_value=1e-10, max_value=1e6, allow_nan=False, allow_infinity=False)


@given(
    slope=small_floats,
    intercept=small_floats,
    n_points=st.integers(min_value=3, max_value=20)
)
def test_perfect_linear_fit(slope, intercept, n_points):
    """Test that ODR can perfectly fit noise-free linear data"""
    # Generate perfect linear data
    x = np.linspace(0, 10, n_points)
    y = slope * x + intercept
    
    # Define linear model
    def linear_func(beta, x):
        return beta[0] * x + beta[1]
    
    # Fit the data
    model = odr.Model(linear_func)
    data = odr.Data(x, y)
    odr_obj = odr.ODR(data, model, beta0=[1.0, 0.0])
    output = odr_obj.run()
    
    # Check that fitted parameters match true parameters
    assert math.isclose(output.beta[0], slope, rel_tol=1e-6, abs_tol=1e-6)
    assert math.isclose(output.beta[1], intercept, rel_tol=1e-6, abs_tol=1e-6)
    
    # Check residuals are near zero
    assert output.res_var < 1e-20


@given(
    x_data=st.lists(valid_floats, min_size=3, max_size=20),
    y_data=st.lists(valid_floats, min_size=3, max_size=20),
    sx=st.lists(positive_floats, min_size=3, max_size=20),
    sy=st.lists(positive_floats, min_size=3, max_size=20)
)
def test_realdata_consistency(x_data, y_data, sx, sy):
    """Test RealData handles standard deviations correctly"""
    # Make all lists same length
    min_len = min(len(x_data), len(y_data), len(sx), len(sy))
    x_data = np.array(x_data[:min_len])
    y_data = np.array(y_data[:min_len])
    sx = np.array(sx[:min_len])
    sy = np.array(sy[:min_len])
    
    # Create RealData with standard deviations
    real_data = odr.RealData(x_data, y_data, sx=sx, sy=sy)
    
    # Properties that should hold
    assert real_data.x.shape == x_data.shape
    assert real_data.y.shape == y_data.shape
    assert np.allclose(real_data.x, x_data)
    assert np.allclose(real_data.y, y_data)
    
    # Weights should be inverse of variance
    if hasattr(real_data, 'wd') and real_data.wd is not None:
        assert real_data.wd.shape[0] == len(x_data)
    if hasattr(real_data, 'we') and real_data.we is not None:
        assert real_data.we.shape[0] == len(y_data)


@given(
    degree=st.integers(min_value=1, max_value=5)
)
def test_polynomial_perfect_fit(degree):
    """Test that polynomial of degree n can fit n+1 points perfectly"""
    # Generate n+1 distinct x points
    n_points = degree + 1
    x = np.linspace(0, 10, n_points)
    
    # Generate random polynomial coefficients
    true_coeffs = np.random.randn(degree + 1)
    
    # Compute y values from polynomial
    y = np.zeros_like(x)
    for i, coeff in enumerate(true_coeffs):
        if i == 0:
            y += coeff
        else:
            y += coeff * (x ** i)
    
    # Fit with ODR polynomial
    poly_model = odr.polynomial(degree)
    data = odr.Data(x, y)
    odr_obj = odr.ODR(data, poly_model, beta0=np.ones(degree + 1))
    output = odr_obj.run()
    
    # Check that fit is perfect (very small residuals)
    assert output.res_var < 1e-15
    assert output.sum_square < 1e-15


@given(
    n_params=st.integers(min_value=1, max_value=10),
    n_data=st.integers(min_value=5, max_value=50)
)
def test_output_dimensions_consistency(n_params, n_data):
    """Test that Output object has consistent dimensions"""
    # Create simple model with n_params parameters
    def model_func(beta, x):
        result = np.zeros_like(x)
        for i, b in enumerate(beta):
            result += b * (x ** i)
        return result
    
    # Generate data
    x = np.linspace(0, 1, n_data)
    y = np.random.randn(n_data)
    
    # Fit model
    model = odr.Model(model_func)
    data = odr.Data(x, y)
    beta0 = np.ones(n_params)
    odr_obj = odr.ODR(data, model, beta0=beta0)
    output = odr_obj.run()
    
    # Check dimensions
    assert output.beta.shape == (n_params,)
    assert output.sd_beta.shape == (n_params,)
    assert output.cov_beta.shape == (n_params, n_params)
    
    # Covariance matrix should be symmetric
    assert np.allclose(output.cov_beta, output.cov_beta.T)
    
    # Check other arrays have correct size
    assert output.xplus.shape == (n_data,)
    assert output.y.shape == (n_data,)
    assert output.delta.shape == (n_data,)
    assert output.eps.shape == (n_data,)


@given(
    x_val=small_floats,
    coeffs=st.lists(small_floats, min_size=2, max_size=5)
)
def test_prebuilt_models_evaluation(x_val, coeffs):
    """Test that pre-built models evaluate without errors"""
    x = np.array([x_val])
    
    # Test exponential model (needs 2 parameters)
    if len(coeffs) >= 2:
        beta_exp = coeffs[:2]
        result = odr.exponential.fcn(beta_exp, x)
        assert result.shape == x.shape
        assert not np.any(np.isnan(result))
    
    # Test quadratic model (needs 3 parameters)
    if len(coeffs) >= 3:
        beta_quad = coeffs[:3]
        result = odr.quadratic.fcn(beta_quad, x)
        assert result.shape == x.shape
        assert not np.any(np.isnan(result))
    
    # Test unilinear model (needs 2 parameters)
    if len(coeffs) >= 2:
        beta_lin = coeffs[:2]
        result = odr.unilinear.fcn(beta_lin, x)
        assert result.shape == x.shape
        assert not np.any(np.isnan(result))


@given(
    x_list=st.lists(small_floats, min_size=2, max_size=10, unique=True)
)
def test_polynomial_factory_consistency(x_list):
    """Test that polynomial factory creates consistent models"""
    degrees = list(range(1, min(len(x_list), 6)))
    
    for degree in degrees:
        # Create polynomial model
        poly = odr.polynomial(degree)
        
        # Check that it's a Model instance
        assert isinstance(poly, odr.Model)
        
        # Test with random coefficients
        beta = np.random.randn(degree + 1)
        x = np.array(x_list)
        
        # Evaluate should work
        result = poly.fcn(beta, x)
        assert result.shape == x.shape
        assert not np.any(np.isnan(result))
        
        # If jacobians exist, they should return correct shapes
        if poly.fjacb is not None:
            jac_b = poly.fjacb(beta, x)
            assert jac_b.shape == (len(x), degree + 1)
        
        if poly.fjacd is not None:
            jac_d = poly.fjacd(beta, x)
            assert jac_d.shape == (len(x),)


@given(
    data_arrays=st.lists(
        st.lists(valid_floats, min_size=3, max_size=20),
        min_size=2, max_size=2
    )
)
def test_data_class_properties(data_arrays):
    """Test Data class handles various input formats correctly"""
    x_data = np.array(data_arrays[0])
    y_data = np.array(data_arrays[1][:len(x_data)])  # Ensure same length
    
    # Test basic Data creation
    data = odr.Data(x_data, y_data)
    
    # Check that data is stored correctly
    assert hasattr(data, 'x')
    assert hasattr(data, 'y')
    assert np.allclose(data.x, x_data)
    assert np.allclose(data.y, y_data)
    
    # Test with weights
    we = np.ones(len(y_data))
    wd = np.ones(len(x_data))
    data_weighted = odr.Data(x_data, y_data, we=we, wd=wd)
    
    assert hasattr(data_weighted, 'we')
    assert hasattr(data_weighted, 'wd')


@given(
    n_points=st.integers(min_value=10, max_value=100),
    noise_level=st.floats(min_value=0.0, max_value=0.1)
)
def test_odr_vs_ols_with_no_x_errors(n_points, noise_level):
    """When x has no errors, ODR should give similar results to OLS"""
    # Generate data with only y errors
    x = np.linspace(0, 10, n_points)
    true_slope = 2.0
    true_intercept = 1.0
    y = true_slope * x + true_intercept + np.random.normal(0, noise_level, n_points)
    
    # Fit with ODR (no x errors)
    def linear_func(beta, x):
        return beta[0] * x + beta[1]
    
    model = odr.Model(linear_func)
    data = odr.Data(x, y)
    odr_obj = odr.ODR(data, model, beta0=[1.0, 0.0])
    odr_output = odr_obj.run()
    
    # Simple least squares solution
    A = np.vstack([x, np.ones(len(x))]).T
    ols_params = np.linalg.lstsq(A, y, rcond=None)[0]
    
    # ODR and OLS should be very close when there's no x error
    assert math.isclose(odr_output.beta[0], ols_params[0], rel_tol=0.01, abs_tol=0.01)
    assert math.isclose(odr_output.beta[1], ols_params[1], rel_tol=0.01, abs_tol=0.01)


@given(
    beta=st.lists(small_floats, min_size=2, max_size=4),
    x=st.floats(min_value=-10, max_value=10, allow_nan=False, allow_infinity=False),
    h=st.floats(min_value=1e-8, max_value=1e-6)
)
def test_jacobian_consistency(beta, x, h):
    """Test that analytical jacobians match numerical differentiation"""
    beta = np.array(beta)
    x_arr = np.array([x])
    
    # Test quadratic model jacobians
    if len(beta) >= 3:
        beta_quad = beta[:3]
        
        # Analytical jacobian
        analytical_jac = odr.quadratic.fjacb(beta_quad, x_arr)
        
        # Numerical jacobian
        numerical_jac = np.zeros_like(analytical_jac)
        for i in range(3):
            beta_plus = beta_quad.copy()
            beta_minus = beta_quad.copy()
            beta_plus[i] += h
            beta_minus[i] -= h
            
            f_plus = odr.quadratic.fcn(beta_plus, x_arr)
            f_minus = odr.quadratic.fcn(beta_minus, x_arr)
            numerical_jac[:, i] = (f_plus - f_minus) / (2 * h)
        
        # Check they're close
        assert np.allclose(analytical_jac, numerical_jac, rtol=1e-4, atol=1e-6)