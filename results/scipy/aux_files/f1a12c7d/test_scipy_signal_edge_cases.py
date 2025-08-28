import numpy as np
import scipy.signal as sig
from hypothesis import given, strategies as st, assume, settings
import pytest
import math


@given(st.integers(min_value=1, max_value=100))
@settings(max_examples=100)
def test_hilbert_analytic_signal_property(n):
    """Test that Hilbert transform produces correct analytic signal."""
    # Create a real signal
    t = np.linspace(0, 1, n)
    freq = 5.0
    x = np.cos(2 * np.pi * freq * t)
    
    # Compute Hilbert transform
    analytic = sig.hilbert(x)
    
    # The real part should be the original signal
    assert np.allclose(np.real(analytic), x, rtol=1e-10, atol=1e-12)
    
    # For a cosine, the imaginary part should be approximately sine
    expected_imag = np.sin(2 * np.pi * freq * t)
    
    # The Hilbert transform of cos is sin (for single frequency)
    # But edge effects make this not exact, so we check the middle portion
    if n > 20:
        middle_slice = slice(n//4, 3*n//4)
        assert np.allclose(np.imag(analytic[middle_slice]), 
                          expected_imag[middle_slice], 
                          rtol=0.1, atol=0.1)


@given(
    st.lists(st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
             min_size=1, max_size=20)
)
@settings(max_examples=100)
def test_detrend_removes_mean(x):
    """Test that detrend with type='constant' removes the mean."""
    if len(x) == 1:
        # Single element arrays have special behavior
        return
    
    detrended = sig.detrend(x, type='constant')
    
    # After detrending, mean should be approximately zero
    assert abs(np.mean(detrended)) < 1e-10


@given(
    st.lists(st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
             min_size=2, max_size=20)
)
@settings(max_examples=100)
def test_detrend_linear_removes_trend(x):
    """Test that detrend with type='linear' removes linear trend."""
    if len(x) < 2:
        return
    
    detrended = sig.detrend(x, type='linear')
    
    # Fit a line to the detrended data
    t = np.arange(len(x))
    coeffs = np.polyfit(t, detrended, 1)
    
    # The slope should be approximately zero
    assert abs(coeffs[0]) < 1e-10


@given(st.integers(min_value=2, max_value=100))
@settings(max_examples=100)
def test_square_wave_duty_cycle(n):
    """Test that square wave has correct duty cycle."""
    t = np.linspace(0, 2, n)
    
    # Test 50% duty cycle (default)
    wave = sig.square(2 * np.pi * t)
    positive = np.sum(wave > 0)
    negative = np.sum(wave < 0)
    
    # Should be approximately equal for 50% duty cycle
    if n > 10:
        ratio = positive / (positive + negative)
        assert 0.4 < ratio < 0.6
    
    # Test 25% duty cycle
    wave25 = sig.square(2 * np.pi * t, duty=0.25)
    positive25 = np.sum(wave25 > 0)
    total = len(wave25)
    
    if n > 10:
        ratio25 = positive25 / total
        assert 0.15 < ratio25 < 0.35


@given(st.integers(min_value=10, max_value=100))
@settings(max_examples=100)
def test_sawtooth_range(n):
    """Test that sawtooth wave stays in [-1, 1] range."""
    t = np.linspace(0, 4, n)
    wave = sig.sawtooth(2 * np.pi * t)
    
    assert np.all(wave >= -1.0)
    assert np.all(wave <= 1.0)
    
    # Test that it actually reaches both extremes
    assert np.any(wave > 0.9)
    assert np.any(wave < -0.9)


@given(
    st.lists(st.floats(min_value=0.1, max_value=10, allow_nan=False, allow_infinity=False),
             min_size=3, max_size=10)
)
@settings(max_examples=100)
def test_find_peaks_basic_property(x):
    """Test that find_peaks finds local maxima correctly."""
    peaks, _ = sig.find_peaks(x)
    
    # Each peak should be a local maximum
    for peak in peaks:
        if 0 < peak < len(x) - 1:
            assert x[peak] >= x[peak - 1]
            assert x[peak] >= x[peak + 1]


@given(
    st.lists(st.floats(min_value=-10, max_value=10, allow_nan=False, allow_infinity=False),
             min_size=1, max_size=20),
    st.lists(st.floats(min_value=-10, max_value=10, allow_nan=False, allow_infinity=False),
             min_size=1, max_size=20)
)
@settings(max_examples=100)
def test_fftconvolve_matches_convolve(a, b):
    """Test that fftconvolve produces same result as convolve."""
    result_direct = sig.convolve(a, b, mode='full')
    result_fft = sig.fftconvolve(a, b, mode='full')
    
    assert len(result_direct) == len(result_fft)
    assert np.allclose(result_direct, result_fft, rtol=1e-9, atol=1e-10)


@given(st.integers(min_value=2, max_value=100))
@settings(max_examples=100)
def test_chirp_frequency_increases(n):
    """Test that chirp signal frequency increases over time."""
    t = np.linspace(0, 1, n)
    f0 = 1  # Start frequency
    f1 = 10  # End frequency
    
    chirp = sig.chirp(t, f0, 1, f1, method='linear')
    
    # Check that signal is bounded
    assert np.all(np.abs(chirp) <= 1.0)
    
    # For linear chirp, instantaneous frequency should increase
    # We can't easily test the exact frequency, but we can check
    # that zero crossings become more frequent
    if n > 20:
        # Count zero crossings in first and last quarters
        first_quarter = chirp[:n//4]
        last_quarter = chirp[3*n//4:]
        
        # Count sign changes
        first_crossings = np.sum(np.diff(np.sign(first_quarter)) != 0)
        last_crossings = np.sum(np.diff(np.sign(last_quarter)) != 0)
        
        # Last quarter should have more crossings (higher frequency)
        # This might not always hold for small n, so we're lenient
        if n > 50:
            assert last_crossings >= first_crossings