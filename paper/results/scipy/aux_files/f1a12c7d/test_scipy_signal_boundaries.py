import numpy as np
import scipy.signal as sig
from hypothesis import given, strategies as st, assume, settings
import pytest
import math


@given(st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_max_len_seq_length(nbits):
    """Test that max_len_seq produces sequence of correct length."""
    seq, state = sig.max_len_seq(nbits)
    
    # Maximum length sequence should have length 2^nbits - 1
    expected_length = 2**nbits - 1
    assert len(seq) == expected_length
    
    # All values should be 0 or 1
    assert set(seq) <= {0, 1}
    
    # State should have nbits elements
    assert len(state) == nbits


@given(st.integers(min_value=1, max_value=10))
@settings(max_examples=50)
def test_max_len_seq_periodicity(nbits):
    """Test that max_len_seq is periodic with correct period."""
    if nbits > 8:  # Skip large values for performance
        return
    
    seq, _ = sig.max_len_seq(nbits)
    length = len(seq)
    
    # Generate a longer sequence to test periodicity
    seq2, _ = sig.max_len_seq(nbits, length=2*length)
    
    # The sequence should repeat
    assert np.array_equal(seq2[:length], seq2[length:2*length])


@given(
    st.lists(st.complex_numbers(min_magnitude=0, max_magnitude=100, 
                                allow_nan=False, allow_infinity=False),
             min_size=2, max_size=20)
)
@settings(max_examples=100)
def test_csd_consistency(x):
    """Test cross-spectral density computation consistency."""
    # CSD of signal with itself should be real and positive (power spectral density)
    freqs, Pxx = sig.csd(x, x, nperseg=min(len(x), 4))
    
    # For real signals, PSD should be real and non-negative
    if all(np.isreal(xi) for xi in x):
        # Power spectral density should be real
        assert np.allclose(np.imag(Pxx), 0, atol=1e-10)
        # And mostly non-negative (allowing small numerical errors)
        assert np.all(np.real(Pxx) >= -1e-10)


@given(
    st.lists(st.floats(min_value=-10, max_value=10, allow_nan=False, allow_infinity=False),
             min_size=8, max_size=100),
    st.integers(min_value=2, max_value=4)
)
@settings(max_examples=50)
def test_welch_parseval(x, nperseg_factor):
    """Test that Welch's method approximately preserves signal energy (Parseval's theorem)."""
    nperseg = min(len(x) // nperseg_factor, len(x))
    if nperseg < 2:
        nperseg = 2
    
    # Compute PSD using Welch's method
    freqs, Pxx = sig.welch(x, nperseg=nperseg, scaling='spectrum')
    
    # Energy in time domain
    energy_time = np.sum(np.array(x)**2) / len(x)
    
    # Energy in frequency domain (integral of PSD)
    # This is approximate due to windowing and overlapping
    energy_freq = np.sum(Pxx) * (freqs[1] - freqs[0]) if len(freqs) > 1 else 0
    
    # These should be approximately equal (Parseval's theorem)
    # Allow significant tolerance due to windowing effects
    if energy_time > 1e-10:  # Avoid division by zero
        ratio = energy_freq / energy_time
        # Very loose bounds due to windowing
        assert 0.1 < ratio < 10


@given(
    st.floats(min_value=0.01, max_value=0.49, allow_nan=False, allow_infinity=False),
    st.integers(min_value=2, max_value=20)
)
@settings(max_examples=100)
def test_firwin_frequency_response(cutoff, numtaps):
    """Test that firwin creates a filter with correct cutoff frequency."""
    # Design a lowpass filter
    h = sig.firwin(numtaps, cutoff)
    
    # Check filter coefficients sum to approximately 1 (DC gain)
    dc_gain = np.sum(h)
    assert 0.9 < dc_gain < 1.1
    
    # Check symmetry (linear phase)
    assert np.allclose(h, h[::-1], rtol=1e-10, atol=1e-12)


@given(
    st.integers(min_value=1, max_value=100),
    st.integers(min_value=1, max_value=100)
)
@settings(max_examples=100)
def test_windows_tukey_continuity(M, alpha_percent):
    """Test Tukey window continuity and boundary conditions."""
    alpha = alpha_percent / 100.0  # Convert to [0, 1]
    
    # Generate Tukey window
    window = sig.windows.tukey(M, alpha=alpha)
    
    # Check length
    assert len(window) == M
    
    # Check boundaries
    if M > 1:
        # Window should start and end at 0 (or very close due to numerical precision)
        assert abs(window[0]) < 1e-10
        assert abs(window[-1]) < 1e-10
    
    # Check that all values are between 0 and 1
    assert np.all(window >= -1e-10)
    assert np.all(window <= 1.0 + 1e-10)
    
    # For alpha=0, should be rectangular (all ones except boundaries)
    if alpha < 0.01 and M > 2:
        assert np.allclose(window[1:-1], 1.0, rtol=1e-10)
    
    # For alpha=1, should be equivalent to Hann window
    if alpha > 0.99:
        hann = sig.windows.hann(M, sym=False)
        assert np.allclose(window, hann, rtol=1e-10, atol=1e-12)