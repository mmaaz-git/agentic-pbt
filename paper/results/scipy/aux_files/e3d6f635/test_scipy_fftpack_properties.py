import numpy as np
import scipy.fftpack
from hypothesis import given, strategies as st, settings, assume
import pytest

# Strategy for reasonable array sizes
reasonable_sizes = st.integers(min_value=1, max_value=1000)

# Strategy for safe floats (avoid NaN and inf)
safe_floats = st.floats(
    allow_nan=False, 
    allow_infinity=False, 
    min_value=-1e6, 
    max_value=1e6
)

# Strategy for 1D float arrays
@st.composite
def float_arrays(draw, min_size=1, max_size=1000):
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    elements = draw(st.lists(safe_floats, min_size=size, max_size=size))
    return np.array(elements, dtype=np.float64)

# Strategy for 1D complex arrays
@st.composite
def complex_arrays(draw, min_size=1, max_size=1000):
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    real_parts = draw(st.lists(safe_floats, min_size=size, max_size=size))
    imag_parts = draw(st.lists(safe_floats, min_size=size, max_size=size))
    return np.array([complex(r, i) for r, i in zip(real_parts, imag_parts)], dtype=np.complex128)

# Strategy for 2D arrays
@st.composite
def float_2d_arrays(draw, min_size=1, max_size=50):
    rows = draw(st.integers(min_value=min_size, max_value=max_size))
    cols = draw(st.integers(min_value=min_size, max_value=max_size))
    elements = draw(st.lists(
        st.lists(safe_floats, min_size=cols, max_size=cols),
        min_size=rows, max_size=rows
    ))
    return np.array(elements, dtype=np.float64)


# Test 1: FFT/IFFT round-trip property
@given(complex_arrays())
@settings(max_examples=100)
def test_fft_ifft_round_trip(x):
    """Test that ifft(fft(x)) == x within numerical tolerance."""
    fft_result = scipy.fftpack.fft(x)
    round_trip = scipy.fftpack.ifft(fft_result)
    np.testing.assert_allclose(round_trip, x, rtol=1e-10, atol=1e-10)


# Test 2: RFFT/IRFFT round-trip for real inputs
@given(float_arrays())
@settings(max_examples=100)
def test_rfft_irfft_round_trip(x):
    """Test that irfft(rfft(x)) == x for real inputs."""
    rfft_result = scipy.fftpack.rfft(x)
    round_trip = scipy.fftpack.irfft(rfft_result, n=len(x))
    np.testing.assert_allclose(round_trip, x, rtol=1e-10, atol=1e-10)


# Test 3: DCT/IDCT round-trip property
@given(float_arrays(), st.sampled_from([1, 2, 3, 4]))
@settings(max_examples=100)
def test_dct_idct_round_trip(x, dct_type):
    """Test that idct(dct(x)) == x for all DCT types."""
    # DCT type 1 requires length > 1
    if dct_type == 1 and len(x) <= 1:
        assume(False)
    
    dct_result = scipy.fftpack.dct(x, type=dct_type)
    round_trip = scipy.fftpack.idct(dct_result, type=dct_type)
    np.testing.assert_allclose(round_trip, x, rtol=1e-10, atol=1e-10)


# Test 4: DST/IDST round-trip property
@given(float_arrays(), st.sampled_from([1, 2, 3, 4]))
@settings(max_examples=100)
def test_dst_idst_round_trip(x, dst_type):
    """Test that idst(dst(x)) == x for all DST types."""
    # DST type 1 requires length > 1
    if dst_type == 1 and len(x) <= 1:
        assume(False)
        
    dst_result = scipy.fftpack.dst(x, type=dst_type)
    round_trip = scipy.fftpack.idst(dst_result, type=dst_type)
    np.testing.assert_allclose(round_trip, x, rtol=1e-10, atol=1e-10)


# Test 5: 2D FFT/IFFT round-trip
@given(float_2d_arrays())
@settings(max_examples=50)
def test_fft2_ifft2_round_trip(x):
    """Test that ifft2(fft2(x)) == x for 2D arrays."""
    fft2_result = scipy.fftpack.fft2(x)
    round_trip = scipy.fftpack.ifft2(fft2_result)
    np.testing.assert_allclose(round_trip, x, rtol=1e-10, atol=1e-10)


# Test 6: FFT linearity property
@given(complex_arrays(), complex_arrays(), safe_floats, safe_floats)
@settings(max_examples=50)
def test_fft_linearity(x, y, a, b):
    """Test FFT linearity: fft(a*x + b*y) == a*fft(x) + b*fft(y)"""
    assume(len(x) == len(y))
    
    # Compute FFT of linear combination
    linear_combo = a * x + b * y
    fft_combo = scipy.fftpack.fft(linear_combo)
    
    # Compute linear combination of FFTs
    fft_x = scipy.fftpack.fft(x)
    fft_y = scipy.fftpack.fft(y)
    combo_fft = a * fft_x + b * fft_y
    
    np.testing.assert_allclose(fft_combo, combo_fft, rtol=1e-10, atol=1e-10)


# Test 7: Parseval's theorem (energy conservation)
@given(complex_arrays())
@settings(max_examples=100)
def test_parseval_theorem(x):
    """Test Parseval's theorem: sum(|x|^2) == sum(|fft(x)|^2) / N"""
    energy_time = np.sum(np.abs(x)**2)
    
    fft_x = scipy.fftpack.fft(x)
    energy_freq = np.sum(np.abs(fft_x)**2) / len(x)
    
    np.testing.assert_allclose(energy_time, energy_freq, rtol=1e-10, atol=1e-10)


# Test 8: DCT orthogonality with 'ortho' normalization
@given(float_arrays(min_size=2))
@settings(max_examples=100)
def test_dct_orthogonality(x):
    """Test that DCT with ortho normalization preserves energy."""
    # DCT-II with ortho normalization
    dct_result = scipy.fftpack.dct(x, type=2, norm='ortho')
    
    # Energy should be preserved
    energy_original = np.sum(x**2)
    energy_transformed = np.sum(dct_result**2)
    
    np.testing.assert_allclose(energy_original, energy_transformed, rtol=1e-10, atol=1e-10)


# Test 9: fftshift and ifftshift are inverses
@given(complex_arrays())
@settings(max_examples=100)
def test_fftshift_ifftshift_round_trip(x):
    """Test that ifftshift(fftshift(x)) == x."""
    shifted = scipy.fftpack.fftshift(x)
    round_trip = scipy.fftpack.ifftshift(shifted)
    np.testing.assert_array_equal(round_trip, x)


# Test 10: Real input to FFT produces conjugate symmetric output
@given(float_arrays())
@settings(max_examples=100)
def test_fft_real_conjugate_symmetry(x):
    """Test that FFT of real input has conjugate symmetry."""
    fft_result = scipy.fftpack.fft(x)
    n = len(fft_result)
    
    # Check conjugate symmetry: X[k] == conj(X[N-k]) for k=1..N/2
    for k in range(1, n//2):
        np.testing.assert_allclose(
            fft_result[k], 
            np.conj(fft_result[n-k]), 
            rtol=1e-10, 
            atol=1e-10
        )