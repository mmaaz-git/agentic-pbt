#!/usr/bin/env python3
"""Minimal reproduction of the bug in calculate_height."""

import sys
import math
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from unittest.mock import patch
from InquirerPy.utils import calculate_height

# Reproduce the bug
with patch("shutil.get_terminal_size") as mock_size:
    # Case 1: When calculation results in exactly 0
    mock_size.return_value = (80, 200)
    
    # 1% of 200 = 2, minus offset of 2 = 0
    result_height, result_max_height = calculate_height("1%", "1%", height_offset=2)
    
    print(f"Test case 1: height=1%, max_height=1%, term_lines=200")
    print(f"  Expected height after clamping: 1 (since 0 should be clamped to 1)")
    print(f"  Actual height: {result_height}")
    print(f"  BUG DETECTED: {result_height == 0}")
    print()
    
    # Case 2: Another example with exactly 0
    mock_size.return_value = (80, 25)
    
    # 12% of 25 = 3, minus offset of 2 = 1 (OK)
    # 8% of 25 = 2, minus offset of 2 = 0 (should be clamped to 1)
    result_height, result_max_height = calculate_height("12%", "8%", height_offset=2)
    
    print(f"Test case 2: height=12%, max_height=8%, term_lines=25")
    print(f"  Height calculation: floor(25 * 0.12) - 2 = 3 - 2 = 1")
    print(f"  Max height calculation: floor(25 * 0.08) - 2 = 2 - 2 = 0 (should be 1)")
    print(f"  Since max_height becomes 1 after clamping, and height(1) <= max_height(1)")
    print(f"  Expected height after clamping to max: 1")
    print(f"  Actual height: {result_height}")
    print(f"  BUG DETECTED: {result_height == 0}")
    print()
    
    # Case 3: When both calculations result in 0
    mock_size.return_value = (80, 25)
    
    # 10% of 25 = 2.5 -> floor = 2, minus offset of 2 = 0
    # 8% of 25 = 2, minus offset of 2 = 0
    result_height, result_max_height = calculate_height("10%", "8%", height_offset=2)
    
    print(f"Test case 3: height=10%, max_height=8%, term_lines=25")
    print(f"  Height calculation: floor(25 * 0.10) - 2 = 2 - 2 = 0")
    print(f"  Max height calculation: floor(25 * 0.08) - 2 = 2 - 2 = 0")
    print(f"  Both should be clamped to 1")
    print(f"  Actual height: {result_height}")
    print(f"  Actual max_height: {result_max_height}")
    print(f"  BUG: Height is {result_height} instead of 1")