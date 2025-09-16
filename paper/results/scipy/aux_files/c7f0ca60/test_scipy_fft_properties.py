import numpy as np
import scipy.fft
from hypothesis import given, strategies as st, settings, assume
import math


# Strategy for reasonable float arrays
@st.composite
def float_arrays(draw, min_size=1, max_size=100):
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    return np.array(draw(st.lists(
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
        min_size=size,
        max_size=size
    )))


@st.composite 
def complex_arrays(draw, min_size=1, max_size=100):
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    reals = draw(st.lists(
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
        min_size=size,
        max_size=size
    ))
    imags = draw(st.lists(
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
        min_size=size,
        max_size=size
    ))
    return np.array([complex(r, i) for r, i in zip(reals, imags)])


@st.composite
def float_2d_arrays(draw, min_size=1, max_size=30):
    rows = draw(st.integers(min_value=min_size, max_value=max_size))
    cols = draw(st.integers(min_value=min_size, max_value=max_size))
    data = draw(st.lists(
        st.lists(
            st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
            min_size=cols,
            max_size=cols
        ),
        min_size=rows,
        max_size=rows
    ))
    return np.array(data)


# Test 1: Round-trip property for fft/ifft - explicitly documented
@given(float_arrays())
@settings(max_examples=500)
def test_fft_ifft_round_trip(x):
    """Test that ifft(fft(x)) == x as documented"""
    fft_result = scipy.fft.fft(x)
    round_trip = scipy.fft.ifft(fft_result)
    np.testing.assert_allclose(round_trip.real, x, rtol=1e-10, atol=1e-10)
    # Imaginary part should be near zero for real input
    np.testing.assert_allclose(round_trip.imag, 0, atol=1e-10)


# Test 2: Round-trip property for complex arrays
@given(complex_arrays())
@settings(max_examples=500)
def test_fft_ifft_complex_round_trip(x):
    """Test that ifft(fft(x)) == x for complex inputs"""
    fft_result = scipy.fft.fft(x)
    round_trip = scipy.fft.ifft(fft_result)
    np.testing.assert_allclose(round_trip, x, rtol=1e-10, atol=1e-10)


# Test 3: Round-trip property for rfft/irfft - explicitly documented
@given(float_arrays())
@settings(max_examples=500)
def test_rfft_irfft_round_trip(x):
    """Test that irfft(rfft(x), len(x)) == x as documented"""
    rfft_result = scipy.fft.rfft(x)
    round_trip = scipy.fft.irfft(rfft_result, n=len(x))
    np.testing.assert_allclose(round_trip, x, rtol=1e-10, atol=1e-10)


# Test 4: Round-trip for 2D FFT - explicitly documented
@given(float_2d_arrays())
@settings(max_examples=200)
def test_fft2_ifft2_round_trip(x):
    """Test that ifft2(fft2(x)) == x as documented"""
    fft2_result = scipy.fft.fft2(x)
    round_trip = scipy.fft.ifft2(fft2_result)
    np.testing.assert_allclose(round_trip.real, x, rtol=1e-10, atol=1e-10)
    np.testing.assert_allclose(round_trip.imag, 0, atol=1e-10)


# Test 5: Round-trip for rfft2/irfft2
@given(float_2d_arrays())
@settings(max_examples=200)
def test_rfft2_irfft2_round_trip(x):
    """Test that irfft2(rfft2(x), x.shape) == x"""
    rfft2_result = scipy.fft.rfft2(x)
    round_trip = scipy.fft.irfft2(rfft2_result, s=x.shape)
    np.testing.assert_allclose(round_trip, x, rtol=1e-10, atol=1e-10)


# Test 6: fftshift/ifftshift inverse property - documented
@given(float_arrays())
@settings(max_examples=500)
def test_fftshift_ifftshift_round_trip(x):
    """Test that ifftshift(fftshift(x)) == x"""
    shifted = scipy.fft.fftshift(x)
    round_trip = scipy.fft.ifftshift(shifted)
    np.testing.assert_array_equal(round_trip, x)


# Test 7: DCT/IDCT round-trip (Type 2 - default)
@given(float_arrays())
@settings(max_examples=500)
def test_dct_idct_round_trip(x):
    """Test that idct(dct(x)) == x for default type 2"""
    dct_result = scipy.fft.dct(x, type=2)
    round_trip = scipy.fft.idct(dct_result, type=2)
    np.testing.assert_allclose(round_trip, x, rtol=1e-10, atol=1e-10)


# Test 8: DST/IDST round-trip (Type 2 - default)
@given(float_arrays(min_size=2))  # DST requires at least 2 elements
@settings(max_examples=500)
def test_dst_idst_round_trip(x):
    """Test that idst(dst(x)) == x for default type 2"""
    dst_result = scipy.fft.dst(x, type=2)
    round_trip = scipy.fft.idst(dst_result, type=2)
    np.testing.assert_allclose(round_trip, x, rtol=1e-10, atol=1e-10)


# Test 9: Linearity property of FFT
@given(float_arrays(), float_arrays(), 
       st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100),
       st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100))
@settings(max_examples=300)
def test_fft_linearity(x, y, a, b):
    """Test that FFT is linear: fft(a*x + b*y) == a*fft(x) + b*fft(y)"""
    assume(len(x) == len(y))  # Arrays must be same size
    
    # Compute fft(a*x + b*y)
    combined = a * x + b * y
    fft_combined = scipy.fft.fft(combined)
    
    # Compute a*fft(x) + b*fft(y)
    fft_x = scipy.fft.fft(x)
    fft_y = scipy.fft.fft(y)
    linear_combination = a * fft_x + b * fft_y
    
    np.testing.assert_allclose(fft_combined, linear_combination, rtol=1e-10, atol=1e-10)


# Test 10: Parseval's theorem - energy conservation
@given(float_arrays())
@settings(max_examples=500)
def test_parseval_theorem(x):
    """Test Parseval's theorem: sum(|x|^2) = sum(|fft(x)|^2) / N"""
    N = len(x)
    energy_time = np.sum(np.abs(x)**2)
    
    fft_result = scipy.fft.fft(x)
    energy_freq = np.sum(np.abs(fft_result)**2) / N
    
    np.testing.assert_allclose(energy_time, energy_freq, rtol=1e-10, atol=1e-10)


# Test 11: FFT with norm parameter consistency
@given(float_arrays())
@settings(max_examples=300)
def test_fft_norm_ortho_round_trip(x):
    """Test that FFT with ortho norm is its own inverse (up to scaling)"""
    fft_ortho = scipy.fft.fft(x, norm='ortho')
    ifft_ortho = scipy.fft.ifft(fft_ortho, norm='ortho')
    np.testing.assert_allclose(ifft_ortho, x, rtol=1e-10, atol=1e-10)


# Test 12: DCT types round-trip
@given(float_arrays(), st.sampled_from([1, 2, 3, 4]))
@settings(max_examples=300)
def test_dct_idct_types(x, dct_type):
    """Test DCT/IDCT round-trip for all types"""
    dct_result = scipy.fft.dct(x, type=dct_type)
    round_trip = scipy.fft.idct(dct_result, type=dct_type)
    np.testing.assert_allclose(round_trip, x, rtol=1e-9, atol=1e-9)


# Test 13: FFT of zero array
@given(st.integers(min_value=1, max_value=100))
@settings(max_examples=100)
def test_fft_zero_array(n):
    """Test FFT of zero array is zero"""
    x = np.zeros(n)
    fft_result = scipy.fft.fft(x)
    np.testing.assert_allclose(fft_result, 0, atol=1e-15)


# Test 14: RFFT output size property
@given(float_arrays())
@settings(max_examples=500)
def test_rfft_output_size(x):
    """Test that rfft output has correct size"""
    n = len(x)
    rfft_result = scipy.fft.rfft(x)
    expected_size = n // 2 + 1
    assert len(rfft_result) == expected_size


# Test 15: Hermitian symmetry for real input
@given(float_arrays(min_size=2))
@settings(max_examples=500)
def test_fft_hermitian_symmetry(x):
    """Test that FFT of real signal has Hermitian symmetry"""
    fft_result = scipy.fft.fft(x)
    n = len(x)
    
    # Check Hermitian symmetry: X[k] = conj(X[N-k]) for k=1..N-1
    for k in range(1, n//2 + 1):
        if n - k < n:  # Ensure we don't go out of bounds
            np.testing.assert_allclose(fft_result[k], np.conj(fft_result[n-k]), rtol=1e-10, atol=1e-10)


# Test 16: Test with specific n parameter in FFT
@given(float_arrays(), st.integers(min_value=1, max_value=200))
@settings(max_examples=300)
def test_fft_with_n_parameter(x, n):
    """Test FFT with explicit n parameter for padding/truncation"""
    fft_result = scipy.fft.fft(x, n=n)
    assert len(fft_result) == n
    
    # Round-trip should work with the same n
    round_trip = scipy.fft.ifft(fft_result, n=n)
    
    # Compare with the appropriately padded/truncated input
    if n > len(x):
        x_padded = np.pad(x, (0, n - len(x)), mode='constant')
        np.testing.assert_allclose(round_trip, x_padded, rtol=1e-10, atol=1e-10)
    else:
        np.testing.assert_allclose(round_trip, x[:n], rtol=1e-10, atol=1e-10)