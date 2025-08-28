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
def test_zpk2tf_tf2zpk_roundtrip(zpk):
    """Test that zpk2tf and tf2zpk are inverse operations."""
    z, p, k = zpk
    
    # Convert zpk to transfer function
    b, a = sig.zpk2tf(z, p, k)
    
    # Convert back to zpk
    z2, p2, k2 = sig.tf2zpk(b, a)
    
    # Check that gain is preserved
    assert math.isclose(k, k2, rel_tol=1e-9, abs_tol=1e-10)
    
    # Check that zeros and poles are preserved (up to ordering)
    # Sort by real part then imaginary part for comparison
    z_sorted = sorted(z, key=lambda x: (x.real, x.imag))
    z2_sorted = sorted(z2, key=lambda x: (x.real, x.imag))
    
    p_sorted = sorted(p, key=lambda x: (x.real, x.imag))
    p2_sorted = sorted(p2, key=lambda x: (x.real, x.imag))
    
    assert len(z_sorted) == len(z2_sorted)
    assert len(p_sorted) == len(p2_sorted)
    
    for z1, z2_val in zip(z_sorted, z2_sorted):
        assert math.isclose(z1.real, z2_val.real, rel_tol=1e-9, abs_tol=1e-10)
        assert math.isclose(z1.imag, z2_val.imag, rel_tol=1e-9, abs_tol=1e-10)
    
    for p1, p2_val in zip(p_sorted, p2_sorted):
        assert math.isclose(p1.real, p2_val.real, rel_tol=1e-9, abs_tol=1e-10)
        assert math.isclose(p1.imag, p2_val.imag, rel_tol=1e-9, abs_tol=1e-10)


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
             min_size=5, max_size=50),
    st.integers(min_value=2, max_value=10)
)
@settings(max_examples=50)
def test_decimate_length_property(x, q):
    """Test that decimate reduces length by approximately factor q."""
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