"""
Property-based tests for numpy.lib.array_utils.normalize_axis_tuple.
Testing axis normalization behavior and edge cases.
"""

import numpy as np
from numpy.lib.array_utils import normalize_axis_tuple
from numpy.exceptions import AxisError
from hypothesis import given, strategies as st, settings, assume
import pytest


@given(
    axis=st.integers(-10, 10),
    ndim=st.integers(1, 10)
)
@settings(max_examples=200)
def test_normalize_single_axis(axis, ndim):
    """Test normalizing a single axis value."""
    
    # Skip invalid cases
    if axis < -ndim or axis >= ndim:
        with pytest.raises((AxisError, IndexError)):
            normalize_axis_tuple(axis, ndim)
        return
    
    result = normalize_axis_tuple(axis, ndim)
    
    # Should return a tuple
    assert isinstance(result, tuple), f"Should return tuple, got {type(result)}"
    assert len(result) == 1, f"Single axis should return 1-element tuple"
    
    # Check normalization
    normalized = result[0]
    if axis < 0:
        expected = axis + ndim
    else:
        expected = axis
    
    assert normalized == expected, \
        f"Normalization failed: axis={axis}, ndim={ndim}, got {normalized}, expected {expected}"
    
    # Result should be in valid range
    assert 0 <= normalized < ndim, \
        f"Normalized axis {normalized} out of range for ndim={ndim}"


@given(
    axes=st.lists(st.integers(-10, 10), min_size=0, max_size=5),
    ndim=st.integers(1, 10)
)
@settings(max_examples=200)
def test_normalize_axis_tuple_multiple(axes, ndim):
    """Test normalizing multiple axes."""
    
    # Check for out of bounds
    has_invalid = any(ax < -ndim or ax >= ndim for ax in axes)
    
    if has_invalid:
        with pytest.raises((AxisError, IndexError)):
            normalize_axis_tuple(axes, ndim)
        return
    
    # Check for duplicates (when allow_duplicate=False, which is default)
    normalized = []
    for ax in axes:
        norm = ax + ndim if ax < 0 else ax
        normalized.append(norm)
    
    if len(normalized) != len(set(normalized)):
        # Has duplicates - raises ValueError, not AxisError
        with pytest.raises(ValueError):
            normalize_axis_tuple(axes, ndim, allow_duplicate=False)
        return
    
    result = normalize_axis_tuple(axes, ndim)
    
    assert isinstance(result, tuple), f"Should return tuple"
    assert len(result) == len(axes), f"Length mismatch"
    
    # Check each normalized axis
    for i, (orig, norm) in enumerate(zip(axes, result)):
        expected = orig + ndim if orig < 0 else orig
        assert norm == expected, f"Axis {i}: {orig} -> {norm}, expected {expected}"
        assert 0 <= norm < ndim, f"Normalized axis {norm} out of range"


@given(
    axes=st.lists(st.integers(-5, 5), min_size=2, max_size=5),
    ndim=st.integers(3, 8)
)
@settings(max_examples=100)
def test_normalize_axis_duplicate_detection(axes, ndim):
    """Test that duplicate axes are properly detected."""
    
    # Create deliberate duplicates
    if len(axes) >= 2 and all(-ndim <= ax < ndim for ax in axes):
        # Make first two axes resolve to the same value
        axes = list(axes)  # Make mutable
        axes[1] = axes[0]
        
        with pytest.raises(ValueError):
            normalize_axis_tuple(axes, ndim, allow_duplicate=False)
        
        # Should work with allow_duplicate=True
        result = normalize_axis_tuple(axes, ndim, allow_duplicate=True)
        assert len(result) == len(axes)




@given(
    axes=st.one_of(
        st.integers(),
        st.lists(st.integers(), min_size=1, max_size=3),
        st.tuples(st.integers(), st.integers())
    ),
    ndim=st.integers(1, 5)
)
@settings(max_examples=100)
def test_normalize_axis_negative_positive_equivalence(axes, ndim):
    """Test that negative and positive indices give equivalent results."""
    
    if isinstance(axes, int):
        axes_list = [axes]
    else:
        axes_list = list(axes)
    
    # Skip invalid
    if any(ax < -ndim or ax >= ndim for ax in axes_list):
        return
    
    # Create equivalent positive indices
    positive_axes = []
    for ax in axes_list:
        if ax < 0:
            positive_axes.append(ax + ndim)
        else:
            positive_axes.append(ax)
    
    # Skip if we'd create duplicates
    if len(positive_axes) != len(set(positive_axes)):
        return
    
    try:
        result1 = normalize_axis_tuple(axes, ndim)
        result2 = normalize_axis_tuple(positive_axes, ndim)
        
        assert result1 == result2, \
            f"Negative and positive forms not equivalent: {axes} -> {result1}, {positive_axes} -> {result2}"
    except AxisError:
        # Both should fail
        with pytest.raises(AxisError):
            normalize_axis_tuple(positive_axes, ndim)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])