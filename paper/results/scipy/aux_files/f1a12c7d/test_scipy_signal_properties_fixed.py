import numpy as np
import scipy.signal as sig
from hypothesis import given, strategies as st, assume, settings
import pytest
import math


# Strategy for generating valid filter coefficients
@st.composite
def zpk_values(draw):
    """Generate valid zero, pole, gain values for transfer functions."""
    n_zeros = draw(st.integers(min_value=0, max_value=5))
    n_poles = draw(st.integers(min_value=1, max_value=5))
    
    # Generate complex zeros and poles
    zeros = draw(st.lists(
        st.complex_numbers(min_magnitude=0, max_magnitude=0.95, allow_nan=False, allow_infinity=False),
        min_size=n_zeros, max_size=n_zeros
    ))
    
    # Poles should be inside unit circle for stability
    poles = draw(st.lists(
        st.complex_numbers(min_magnitude=0, max_magnitude=0.95, allow_nan=False, allow_infinity=False),
        min_size=n_poles, max_size=n_poles
    ))
    
    gain = draw(st.floats(min_value=0.1, max_value=10, allow_nan=False, allow_infinity=False))
    
    return zeros, poles, gain


@given(zpk_values())
@settings(max_examples=100)
def test_zpk2tf_tf2zpk_transfer_function_equivalence(zpk):
    """Test that zpk2tf and tf2zpk preserve the transfer function behavior."""
    z, p, k = zpk
    
    # Convert zpk to transfer function
    b, a = sig.zpk2tf(z, p, k)
    
    # Convert back to zpk
    z2, p2, k2 = sig.tf2zpk(b, a)
    
    # Check that the transfer functions are equivalent by evaluating at test points
    test_points = [1j, 2j, -1j, 1+1j, 2+3j, 0.5+0.5j]
    
    for s in test_points:
        # Evaluate original zpk
        num_orig = k * np.prod([s - zi for zi in z]) if z else k
        den_orig = np.prod([s - pi for pi in p]) if p else 1
        h_orig = num_orig / den_orig if den_orig != 0 else float('inf')
        
        # Evaluate recovered zpk  
        num_rec = k2 * np.prod([s - zi for zi in z2]) if len(z2) > 0 else k2
        den_rec = np.prod([s - pi for pi in p2]) if len(p2) > 0 else 1
        h_rec = num_rec / den_rec if den_rec != 0 else float('inf')
        
        if h_orig != float('inf') and h_rec != float('inf'):
            # Allow for reasonable numerical error
            assert np.allclose(h_orig, h_rec, rtol=1e-10, atol=1e-12)


@given(
    st.lists(st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False), 
             min_size=1, max_size=20),
    st.lists(st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False), 
             min_size=1, max_size=20)
)
@settings(max_examples=100)
def test_convolve_commutativity(a, b):
    """Test that convolution is commutative in 'full' mode."""
    result1 = sig.convolve(a, b, mode='full')
    result2 = sig.convolve(b, a, mode='full')
    
    assert len(result1) == len(result2)
    assert np.allclose(result1, result2, rtol=1e-9, atol=1e-10)


@given(st.lists(st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
                min_size=1, max_size=100))
@settings(max_examples=100) 
def test_unique_roots_idempotence(roots):
    """Test that unique_roots is idempotent."""
    # First application
    unique1, multiplicity1 = sig.unique_roots(roots)
    
    # Second application on the unique roots
    unique2, multiplicity2 = sig.unique_roots(unique1)
    
    # unique_roots applied to already unique roots should return the same
    assert len(unique1) == len(unique2)
    assert np.allclose(sorted(unique1), sorted(unique2), rtol=1e-9, atol=1e-10)
    
    # All multiplicities should be 1 after first application
    assert all(m == 1 for m in multiplicity2)


@given(
    st.lists(st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
             min_size=10, max_size=1000),
    st.integers(min_value=5, max_value=500)
)
@settings(max_examples=50)
def test_resample_length_invariant(x, num):
    """Test that resample produces output of requested length."""
    resampled = sig.resample(x, num)
    assert len(resampled) == num


@given(
    st.lists(st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
             min_size=30, max_size=100),  # Increased min_size to avoid padding issues
    st.integers(min_value=2, max_value=5)  # Reduced max q to avoid excessive padding requirements
)
@settings(max_examples=50)
def test_decimate_length_property(x, q):
    """Test that decimate reduces length by approximately factor q."""
    # The default IIR filter in decimate requires padding
    # For an order 8 Chebyshev filter, the padding is 3 * 9 = 27 samples
    # So we need at least 28 samples
    
    decimated = sig.decimate(x, q)
    
    # The expected length after decimation
    expected_length = int(np.ceil(len(x) / q))
    
    # Allow for off-by-one due to edge effects
    assert abs(len(decimated) - expected_length) <= 1


# Test for window function symmetry
@given(st.integers(min_value=3, max_value=100))
@settings(max_examples=100)
def test_window_symmetry(n):
    """Test that symmetric windows are actually symmetric."""
    window_types = ['hamming', 'hann', 'bartlett', 'blackman']
    
    for window_type in window_types:
        window = sig.get_window(window_type, n, fftbins=False)
        
        # Check symmetry
        assert len(window) == n
        
        # For symmetric windows, window[i] should equal window[n-1-i]
        for i in range(n // 2):
            assert math.isclose(window[i], window[n-1-i], rel_tol=1e-9, abs_tol=1e-10)


@given(
    st.lists(st.floats(min_value=-10, max_value=10, allow_nan=False, allow_infinity=False),
             min_size=2, max_size=10),
    st.lists(st.floats(min_value=-10, max_value=10, allow_nan=False, allow_infinity=False),
             min_size=2, max_size=10)
)
@settings(max_examples=100)
def test_correlate_convolve_relationship(a, b):
    """Test that correlate(a, b) = convolve(a, b[::-1]) for real signals."""
    # This is a documented mathematical relationship
    
    corr_result = sig.correlate(a, b, mode='full')
    conv_result = sig.convolve(a, b[::-1], mode='full')
    
    assert len(corr_result) == len(conv_result)
    assert np.allclose(corr_result, conv_result, rtol=1e-9, atol=1e-10)