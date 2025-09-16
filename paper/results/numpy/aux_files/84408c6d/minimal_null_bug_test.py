import numpy as np
import numpy.strings as ns
from hypothesis import given, strategies as st

@given(st.text(alphabet=st.just('\x00'), min_size=1, max_size=10))
def test_str_len_null_character_bug(s):
    """Test that str_len handles null characters correctly"""
    # Create numpy string array
    arr = np.array([s], dtype=f'U{len(s) + 10}')
    
    # Get length from numpy
    numpy_len = ns.str_len(arr)[0]
    
    # Get expected length from Python
    expected_len = len(s)
    
    # This should be equal but it's not - NumPy treats \x00 as string terminator
    assert numpy_len == expected_len, f"str_len('{repr(s)}') = {numpy_len}, expected {expected_len}"

if __name__ == "__main__":
    # Run the test
    test_str_len_null_character_bug()