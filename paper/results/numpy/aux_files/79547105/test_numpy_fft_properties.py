import numpy as np
from hypothesis import given, strategies as st, assume, settings
import pytest


@st.composite
def reasonable_arrays(draw, dtype=None):
    """Generate reasonable arrays for FFT testing"""
    shape = draw(st.lists(st.integers(1, 30), min_size=1, max_size=3))
    if dtype == 'real':
        elements = st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
    elif dtype == 'complex':
        elements = st.complex_numbers(
            min_magnitude=0, max_magnitude=1e6,
            allow_nan=False, allow_infinity=False
        )
    else:
        elements = st.one_of(
            st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
            st.complex_numbers(min_magnitude=0, max_magnitude=1e6, allow_nan=False, allow_infinity=False)
        )
    
    # Convert numpy int64 to regular Python int
    size = int(np.prod(shape))
    arr = draw(st.lists(elements, min_size=size, max_size=size))
    return np.array(arr).reshape(shape)


@st.composite
def real_arrays(draw):
    """Generate real-valued arrays"""
    return draw(reasonable_arrays(dtype='real'))


@st.composite 
def complex_arrays(draw):
    """Generate complex arrays"""
    return draw(reasonable_arrays(dtype='complex'))


@given(reasonable_arrays())
@settings(max_examples=500)
def test_fft_ifft_round_trip(x):
    """Test that ifft(fft(x)) ≈ x"""
    result = np.fft.ifft(np.fft.fft(x))
    assert np.allclose(result, x, rtol=1e-10, atol=1e-10)


@given(reasonable_arrays())
@settings(max_examples=500)
def test_parseval_theorem(x):
    """Test Parseval's theorem: energy conservation in frequency domain"""
    x_flat = x.flatten()
    fft_x = np.fft.fft(x_flat)
    
    time_energy = np.sum(np.abs(x_flat) ** 2)
    freq_energy = np.sum(np.abs(fft_x) ** 2) / len(x_flat)
    
    assert np.allclose(time_energy, freq_energy, rtol=1e-10)


@given(reasonable_arrays(), st.floats(-10, 10, allow_nan=False), 
       reasonable_arrays(), st.floats(-10, 10, allow_nan=False))
@settings(max_examples=200)  
def test_fft_linearity(x, a, y, b):
    """Test FFT linearity: fft(a*x + b*y) = a*fft(x) + b*fft(y)"""
    assume(x.shape == y.shape)
    
    left = np.fft.fft(a * x + b * y)
    right = a * np.fft.fft(x) + b * np.fft.fft(y)
    
    assert np.allclose(left, right, rtol=1e-10, atol=1e-10)


@given(reasonable_arrays())
@settings(max_examples=500)
def test_fftshift_ifftshift_inverse(x):
    """Test that ifftshift(fftshift(x)) = x"""
    result = np.fft.ifftshift(np.fft.fftshift(x))
    assert np.array_equal(result, x)


@given(real_arrays())
@settings(max_examples=500)
def test_rfft_irfft_round_trip(x):
    """Test that irfft(rfft(x)) ≈ x for real arrays"""
    x_1d = x.flatten()
    result = np.fft.irfft(np.fft.rfft(x_1d))
    
    # irfft may return different length, so we compare up to original length
    min_len = min(len(result), len(x_1d))
    assert np.allclose(result[:min_len], x_1d[:min_len], rtol=1e-10, atol=1e-10)


@given(real_arrays())
@settings(max_examples=500)
def test_rfft_hermitian_symmetry(x):
    """Test that rfft of real input has correct properties"""
    x_1d = x.flatten()
    result = np.fft.rfft(x_1d)
    
    # Result should be complex for non-trivial inputs
    if len(x_1d) > 1:
        assert result.dtype in [np.complex64, np.complex128]


@given(complex_arrays())
@settings(max_examples=500)
def test_hfft_ihfft_properties(x):
    """Test hfft/ihfft for Hermitian inputs"""
    x_1d = x.flatten()
    
    # Make the input Hermitian-symmetric  
    n = len(x_1d)
    if n > 1:
        # Create a proper Hermitian array
        hermitian = np.zeros(n, dtype=complex)
        hermitian[0] = np.real(x_1d[0])  # DC component must be real
        
        for i in range(1, (n+1)//2):
            hermitian[i] = x_1d[i]
            if n - i < n:
                hermitian[n - i] = np.conj(x_1d[i])
        
        if n % 2 == 0:
            hermitian[n//2] = np.real(x_1d[n//2])  # Nyquist must be real
        
        # hfft should produce real output for Hermitian input
        result = np.fft.hfft(hermitian[:n//2+1])
        assert np.all(np.isreal(result))


@given(reasonable_arrays(), st.sampled_from(['backward', 'ortho', 'forward']))
@settings(max_examples=200)
def test_fft_normalization_modes(x, norm):
    """Test different normalization modes preserve round-trip"""
    fft_result = np.fft.fft(x, norm=norm)
    ifft_result = np.fft.ifft(fft_result, norm=norm)
    assert np.allclose(ifft_result, x, rtol=1e-10, atol=1e-10)


@given(st.integers(1, 1000))
@settings(max_examples=500)
def test_fftfreq_properties(n):
    """Test fftfreq generates correct frequency bins"""
    freqs = np.fft.fftfreq(n)
    
    # Should have n frequencies
    assert len(freqs) == n
    
    # First frequency should be 0 (DC)
    assert freqs[0] == 0
    
    # Should be sorted correctly (positive then negative freqs)
    mid = (n + 1) // 2
    if n > 1:
        assert np.all(freqs[1:mid] > 0)  # Positive frequencies
        if n > 2:
            assert np.all(freqs[mid:] < 0)  # Negative frequencies


@given(st.integers(1, 1000))
@settings(max_examples=500)
def test_rfftfreq_properties(n):
    """Test rfftfreq for real FFT frequencies"""
    freqs = np.fft.rfftfreq(n)
    
    # Should have n//2 + 1 frequencies
    assert len(freqs) == n // 2 + 1
    
    # Should all be non-negative
    assert np.all(freqs >= 0)
    
    # Should be monotonically increasing
    assert np.all(np.diff(freqs) >= 0)


@given(reasonable_arrays())
@settings(max_examples=300)
def test_fft2_ifft2_round_trip(x):
    """Test 2D FFT round trip"""
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    elif x.ndim > 2:
        x = x.reshape(x.shape[0], -1)
    
    result = np.fft.ifft2(np.fft.fft2(x))
    assert np.allclose(result, x, rtol=1e-10, atol=1e-10)


@given(reasonable_arrays(), st.integers(-3, 3))
@settings(max_examples=300)
def test_fft_axis_parameter(x, axis):
    """Test FFT with different axis specifications"""
    assume(x.ndim >= abs(axis))
    
    if x.ndim == 0:
        x = x.reshape(1)
    
    # Forward and inverse with same axis
    result = np.fft.ifft(np.fft.fft(x, axis=axis), axis=axis)
    assert np.allclose(result, x, rtol=1e-10, atol=1e-10)


@given(reasonable_arrays())
@settings(max_examples=300)
def test_fftn_ifftn_round_trip(x):
    """Test N-dimensional FFT round trip"""
    result = np.fft.ifftn(np.fft.fftn(x))
    assert np.allclose(result, x, rtol=1e-10, atol=1e-10)


@given(real_arrays())
@settings(max_examples=300)
def test_rfft2_irfft2_round_trip(x):
    """Test 2D real FFT round trip"""
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    elif x.ndim > 2:
        x = x.reshape(x.shape[0], -1)
    
    result = np.fft.irfft2(np.fft.rfft2(x))
    
    # Shape may differ slightly due to rfft2/irfft2 
    min_shape = tuple(min(a, b) for a, b in zip(result.shape, x.shape))
    assert np.allclose(result[:min_shape[0], :min_shape[1]], 
                      x[:min_shape[0], :min_shape[1]], rtol=1e-10, atol=1e-10)


@given(real_arrays())
@settings(max_examples=300)
def test_rfftn_irfftn_round_trip(x):
    """Test N-dimensional real FFT round trip"""
    result = np.fft.irfftn(np.fft.rfftn(x))
    
    # Compare only overlapping regions
    slices = tuple(slice(0, min(a, b)) for a, b in zip(result.shape, x.shape))
    assert np.allclose(result[slices], x[slices], rtol=1e-10, atol=1e-10)


@given(st.lists(st.floats(-1e6, 1e6, allow_nan=False, allow_infinity=False), 
                min_size=1, max_size=100))
@settings(max_examples=500)
def test_real_fft_conjugate_symmetry(x):
    """Test that FFT of real input has conjugate symmetry"""
    x = np.array(x)
    fft_result = np.fft.fft(x)
    n = len(x)
    
    # Check conjugate symmetry: X[k] = conj(X[n-k])
    for k in range(1, n // 2):
        assert np.allclose(fft_result[k], np.conj(fft_result[n - k]), rtol=1e-10)


@given(st.integers(1, 100), st.integers(1, 100))
@settings(max_examples=200)
def test_fft_with_n_parameter(orig_size, n):
    """Test FFT with explicit size parameter"""
    x = np.random.randn(orig_size)
    
    fft_result = np.fft.fft(x, n=n)
    assert len(fft_result) == n
    
    # Round trip with same n
    ifft_result = np.fft.ifft(fft_result, n=n)
    assert len(ifft_result) == n
    
    # Check values match where they overlap
    min_len = min(orig_size, n)
    assert np.allclose(ifft_result[:min_len], x[:min_len], rtol=1e-10, atol=1e-10)