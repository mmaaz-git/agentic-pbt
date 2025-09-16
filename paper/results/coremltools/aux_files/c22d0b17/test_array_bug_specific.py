#!/usr/bin/env python3
"""Specific test cases demonstrating the Array dimension validation bug"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

from coremltools.models import datatypes

def test_specific_cases():
    # Case 1: Zero dimension
    arr1 = datatypes.Array(0)
    print(f"Bug: Array(0) created with num_elements={arr1.num_elements}")
    assert arr1.num_elements == 0  # This shouldn't be allowed
    
    # Case 2: Negative dimension
    arr2 = datatypes.Array(-5)
    print(f"Bug: Array(-5) created with num_elements={arr2.num_elements}")
    assert arr2.num_elements == -5  # This is nonsensical!
    
    # Case 3: Mixed dimensions with zero
    arr3 = datatypes.Array(3, 0, 5)
    print(f"Bug: Array(3, 0, 5) created with num_elements={arr3.num_elements}")
    assert arr3.num_elements == 0  # Product includes zero
    
    # Case 4: Multiple negative dimensions
    arr4 = datatypes.Array(-2, -3)
    print(f"Bug: Array(-2, -3) created with num_elements={arr4.num_elements}")
    assert arr4.num_elements == 6  # Product of negatives is positive but dimensions are still invalid

if __name__ == "__main__":
    test_specific_cases()
    print("\nAll assertions passed - these Arrays were created with invalid dimensions!")