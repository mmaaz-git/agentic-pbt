"""Property-based tests for InquirerPy.utils module - Fixed version."""

import math
import os
import shutil
from unittest.mock import patch

from hypothesis import assume, given, settings, strategies as st
from InquirerPy.exceptions import InvalidArgument
from InquirerPy.utils import InquirerPyStyle, calculate_height, get_style


@given(
    height_percent=st.integers(min_value=1, max_value=200),
    max_height_percent=st.integers(min_value=1, max_value=200),
    term_lines=st.integers(min_value=10, max_value=1000),
)
def test_calculate_height_percentage_calculation_bug(height_percent, max_height_percent, term_lines):
    """Test that percentage strings are correctly converted to line counts.
    
    This test reveals a bug in the calculate_height function.
    """
    with patch("shutil.get_terminal_size") as mock_size:
        mock_size.return_value = (80, term_lines)
        
        height_str = f"{height_percent}%"
        max_height_str = f"{max_height_percent}%"
        
        result_height, result_max_height = calculate_height(
            height_str, max_height_str, height_offset=2
        )
        
        # Calculate expected values based on the documented behavior
        expected_height = math.floor(term_lines * (height_percent / 100)) - 2
        expected_max_height = math.floor(term_lines * (max_height_percent / 100)) - 2
        
        # The code claims to clamp values to at least 1 (lines 232-235)
        # Let's see if it actually does this correctly
        print(f"Input: height={height_percent}%, max_height={max_height_percent}%, term_lines={term_lines}")
        print(f"Expected height before clamping: {expected_height}")
        print(f"Expected max_height before clamping: {expected_max_height}")
        print(f"Actual result_height: {result_height}")
        print(f"Actual result_max_height: {result_max_height}")
        
        # Check if the bug is in the clamping logic
        if expected_height <= 0:
            # The code should set it to 1 according to lines 232-233
            assert result_height == 1, f"Height should be 1 when calculated value is {expected_height}"
        elif expected_height > expected_max_height:
            # The code should clamp to max_height
            if expected_max_height <= 0:
                assert result_height == 1
            else:
                assert result_height == expected_max_height
        else:
            assert result_height == expected_height