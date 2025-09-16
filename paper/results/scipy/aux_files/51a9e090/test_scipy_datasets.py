"""Property-based tests for scipy.datasets module."""

import numpy as np
import scipy.datasets
from hypothesis import given, strategies as st, settings


def test_face_grayscale_conversion_consistency():
    """Test that manual grayscale conversion matches face(gray=True)."""
    # Get the color and grayscale versions
    face_color = scipy.datasets.face(gray=False)
    face_gray_builtin = scipy.datasets.face(gray=True)
    
    # Manually convert color to grayscale using the same formula from source
    face_gray_manual = (0.21 * face_color[:, :, 0] + 
                        0.71 * face_color[:, :, 1] + 
                        0.07 * face_color[:, :, 2]).astype('uint8')
    
    # They should be identical
    assert np.array_equal(face_gray_builtin, face_gray_manual), \
        "Manual grayscale conversion doesn't match face(gray=True)"


def test_ascent_immutability():
    """Test that ascent() returns a copy, not a mutable reference."""
    img1 = scipy.datasets.ascent()
    img2 = scipy.datasets.ascent()
    
    # Modify img1
    original_value = img1[0, 0]
    img1[0, 0] = (img1[0, 0] + 1) % 256
    
    # img2 should not be affected
    assert img2[0, 0] == original_value, \
        "ascent() returns mutable reference instead of copy"
    
    # Fresh call should also return unmodified data
    img3 = scipy.datasets.ascent()
    assert img3[0, 0] == original_value, \
        "ascent() data was permanently modified"


def test_face_immutability():
    """Test that face() returns a copy, not a mutable reference."""
    img1 = scipy.datasets.face(gray=False)
    img2 = scipy.datasets.face(gray=False)
    
    # Modify img1
    original_value = img1[0, 0, 0]
    img1[0, 0, 0] = (img1[0, 0, 0] + 1) % 256
    
    # img2 should not be affected
    assert img2[0, 0, 0] == original_value, \
        "face() returns mutable reference instead of copy"
    
    # Fresh call should also return unmodified data
    img3 = scipy.datasets.face(gray=False)
    assert img3[0, 0, 0] == original_value, \
        "face() data was permanently modified"


def test_electrocardiogram_immutability():
    """Test that electrocardiogram() returns a copy, not a mutable reference."""
    ecg1 = scipy.datasets.electrocardiogram()
    ecg2 = scipy.datasets.electrocardiogram()
    
    # Modify ecg1
    original_value = ecg1[0]
    ecg1[0] = ecg1[0] + 1.0
    
    # ecg2 should not be affected
    assert ecg2[0] == original_value, \
        "electrocardiogram() returns mutable reference instead of copy"
    
    # Fresh call should also return unmodified data
    ecg3 = scipy.datasets.electrocardiogram()
    assert ecg3[0] == original_value, \
        "electrocardiogram() data was permanently modified"


def test_face_gray_parameter_type_handling():
    """Test how face() handles different truthy/falsy values for gray parameter."""
    # Get reference images
    color_ref = scipy.datasets.face(gray=False)
    gray_ref = scipy.datasets.face(gray=True)
    
    # Test various falsy values
    assert np.array_equal(scipy.datasets.face(gray=0), color_ref)
    assert np.array_equal(scipy.datasets.face(gray=None), color_ref)
    assert np.array_equal(scipy.datasets.face(gray=[]), color_ref)
    assert np.array_equal(scipy.datasets.face(gray=""), color_ref)
    
    # Test various truthy values
    assert np.array_equal(scipy.datasets.face(gray=1), gray_ref)
    assert np.array_equal(scipy.datasets.face(gray="yes"), gray_ref)
    assert np.array_equal(scipy.datasets.face(gray=[1]), gray_ref)


@given(st.integers())
def test_face_gray_parameter_integer_values(gray_value):
    """Test face() with arbitrary integer values for gray parameter."""
    # Should work without crashing and return consistent shape
    result = scipy.datasets.face(gray=gray_value)
    
    if gray_value:  # Truthy
        assert result.shape == (768, 1024), \
            f"Unexpected shape for gray={gray_value}: {result.shape}"
    else:  # Falsy (0)
        assert result.shape == (768, 1024, 3), \
            f"Unexpected shape for gray={gray_value}: {result.shape}"
    
    assert result.dtype == np.uint8, \
        f"Unexpected dtype for gray={gray_value}: {result.dtype}"


def test_face_grayscale_weights_sum():
    """Test that the grayscale conversion weights sum to less than 1."""
    # The weights used are 0.21, 0.71, 0.07
    weights_sum = 0.21 + 0.71 + 0.07
    assert abs(weights_sum - 0.99) < 0.001, \
        f"Grayscale weights sum to {weights_sum}, not ~1.0"
    
    # This could lead to the max grayscale value being less than 255
    # Let's verify this mathematically
    max_possible_gray = int(255 * weights_sum)
    assert max_possible_gray == 252, \
        f"Max possible grayscale value is {max_possible_gray}, not 252"
    
    # Check actual max value in the grayscale image
    face_gray = scipy.datasets.face(gray=True)
    actual_max = face_gray.max()
    assert actual_max <= 252, \
        f"Grayscale image has max value {actual_max} > theoretical max 252"


def test_electrocardiogram_sampling_rate_consistency():
    """Test that ECG data length matches documented sampling rate."""
    ecg = scipy.datasets.electrocardiogram()
    
    # Documentation says: 5 minutes at 360 Hz
    expected_samples = 5 * 60 * 360  # 5 minutes * 60 seconds * 360 Hz
    
    assert len(ecg) == expected_samples, \
        f"ECG length {len(ecg)} doesn't match expected {expected_samples} samples"
    
    assert ecg.shape == (expected_samples,), \
        f"ECG shape {ecg.shape} doesn't match expected ({expected_samples},)"


def test_deterministic_behavior():
    """Test that all functions return identical data on multiple calls."""
    # Test ascent
    ascent1 = scipy.datasets.ascent()
    ascent2 = scipy.datasets.ascent()
    assert np.array_equal(ascent1, ascent2), "ascent() is not deterministic"
    
    # Test face (color)
    face1 = scipy.datasets.face(gray=False)
    face2 = scipy.datasets.face(gray=False)
    assert np.array_equal(face1, face2), "face(gray=False) is not deterministic"
    
    # Test face (gray)
    face_gray1 = scipy.datasets.face(gray=True)
    face_gray2 = scipy.datasets.face(gray=True)
    assert np.array_equal(face_gray1, face_gray2), "face(gray=True) is not deterministic"
    
    # Test electrocardiogram
    ecg1 = scipy.datasets.electrocardiogram()
    ecg2 = scipy.datasets.electrocardiogram()
    assert np.array_equal(ecg1, ecg2), "electrocardiogram() is not deterministic"