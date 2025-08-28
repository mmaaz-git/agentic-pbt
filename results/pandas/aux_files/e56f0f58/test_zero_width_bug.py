import pandas as pd
import pandas.arrays as pa
import numpy as np
from hypothesis import given, strategies as st


@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6))
def test_zero_width_interval_contains_bug(point):
    """Test that zero-width intervals properly contain their endpoints based on closed parameter."""
    
    # Test right-closed zero-width interval
    interval_right = pd.Interval(point, point, closed='right')
    assert point in interval_right or interval_right.right in interval_right, \
        f"Right-closed interval {interval_right} should contain its right endpoint {point}"
    
    # Test left-closed zero-width interval
    interval_left = pd.Interval(point, point, closed='left')
    assert point in interval_left or interval_left.left in interval_left, \
        f"Left-closed interval {interval_left} should contain its left endpoint {point}"
    
    # Test both-closed zero-width interval
    interval_both = pd.Interval(point, point, closed='both')
    assert point in interval_both, \
        f"Both-closed interval {interval_both} should contain point {point}"
    
    # Test neither-closed zero-width interval
    interval_neither = pd.Interval(point, point, closed='neither')
    # This should NOT contain the point
    assert point not in interval_neither, \
        f"Neither-closed interval {interval_neither} should not contain point {point}"


@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6))
def test_interval_array_zero_width_contains_bug(point):
    """Test IntervalArray.contains() with zero-width intervals."""
    
    # Create zero-width intervals with different closed parameters
    intervals = [
        pd.Interval(point, point, closed='right'),
        pd.Interval(point, point, closed='left'),
        pd.Interval(point, point, closed='both'),
        pd.Interval(point, point, closed='neither'),
    ]
    
    for i, interval in enumerate(intervals):
        # Test single interval in array
        arr = pa.IntervalArray([interval])
        contains_result = arr.contains(point)[0]
        
        # Check if interval should contain the point
        if interval.closed == 'both':
            assert contains_result == True, \
                f"Both-closed zero-width interval should contain {point}, got {contains_result}"
        elif interval.closed == 'right':
            # Right-closed should contain the right endpoint (which equals point)
            assert contains_result == True, \
                f"Right-closed zero-width interval (={point}, {point}] should contain {point}, got {contains_result}"
        elif interval.closed == 'left':
            # Left-closed should contain the left endpoint (which equals point)
            assert contains_result == True, \
                f"Left-closed zero-width interval [{point}, {point}) should contain {point}, got {contains_result}"
        else:  # neither
            assert contains_result == False, \
                f"Neither-closed zero-width interval should not contain {point}, got {contains_result}"


if __name__ == "__main__":
    # Run specific failing examples
    print("Testing specific failing case:")
    
    # Right-closed zero-width interval
    interval = pd.Interval(0.0, 0.0, closed='right')
    print(f"Interval: {interval}")
    print(f"0.0 in interval: {0.0 in interval}")
    print(f"Expected: True (right endpoint should be included)")
    
    # In IntervalArray
    arr = pa.IntervalArray([interval])
    print(f"\nIntervalArray: {arr}")
    print(f"arr.contains(0.0): {arr.contains(0.0)}")
    print(f"Expected: [True]")
    
    # Left-closed zero-width interval
    interval2 = pd.Interval(0.0, 0.0, closed='left')
    print(f"\nInterval: {interval2}")
    print(f"0.0 in interval: {0.0 in interval2}")
    print(f"Expected: True (left endpoint should be included)")
    
    arr2 = pa.IntervalArray([interval2])
    print(f"\nIntervalArray: {arr2}")
    print(f"arr.contains(0.0): {arr2.contains(0.0)}")
    print(f"Expected: [True]")