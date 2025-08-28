"""
Demonstrate the inconsistent behavior of the start parameter in tenumerate
"""
import numpy as np
from tqdm.contrib import tenumerate


def test_tenumerate_start_parameter_inconsistency():
    """
    The start parameter behaves inconsistently between regular iterables and numpy arrays.
    For regular iterables, it works as expected.
    For numpy arrays, it is silently ignored without warning or error.
    """
    
    # Test with regular list
    regular_list = [10, 20, 30]
    result_list = list(tenumerate(regular_list, start=100))
    print(f"Regular list with start=100: {result_list}")
    # Expected and actual: [(100, 10), (101, 20), (102, 30)]
    assert result_list == [(100, 10), (101, 20), (102, 30)]
    
    # Test with numpy array - start parameter is IGNORED
    numpy_array = np.array([10, 20, 30])
    result_array = list(tenumerate(numpy_array, start=100))
    print(f"NumPy array with start=100: {result_array}")
    # Expected by user: indices starting at 100
    # Actual: indices starting at 0 (start is ignored!)
    
    # This demonstrates the bug: same function, different behavior
    # The start parameter should either:
    # 1. Work for both (preferred)
    # 2. Raise an error for numpy arrays if not supported
    # 3. Be documented clearly that it doesn't work for numpy arrays
    
    # Current behavior: silently ignored, which is confusing
    assert result_array[0][0] == (0,)  # First index is (0,) not (100,)
    assert result_array[1][0] == (1,)  # Second index is (1,) not (101,)
    
    print("\nBUG: The 'start' parameter is silently ignored for numpy arrays!")
    print("This violates the principle of least surprise.")
    return False  # Indicating this is problematic behavior


if __name__ == "__main__":
    test_tenumerate_start_parameter_inconsistency()