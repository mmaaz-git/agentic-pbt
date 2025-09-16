#!/usr/bin/env python3
"""Runner script for property-based tests."""

import sys
import traceback

# Import test functions
from test_praw_const import (
    test_image_headers_are_valid_bytes,
    test_image_size_constants_relationships,
    test_version_format,
    test_user_agent_format_is_valid_format_string,
    test_api_path_is_dictionary,
    test_jpeg_header_detection,
    test_png_header_detection,
    test_size_validation_logic
)

from hypothesis import given, strategies as st, settings
import praw.const as const

def run_tests():
    """Run all tests and report results."""
    tests = [
        ("test_image_headers_are_valid_bytes", test_image_headers_are_valid_bytes),
        ("test_image_size_constants_relationships", test_image_size_constants_relationships),
        ("test_version_format", test_version_format),
        ("test_api_path_is_dictionary", test_api_path_is_dictionary),
    ]
    
    hypothesis_tests = [
        ("test_user_agent_format_is_valid_format_string", test_user_agent_format_is_valid_format_string),
        ("test_jpeg_header_detection", test_jpeg_header_detection),
        ("test_png_header_detection", test_png_header_detection),
        ("test_size_validation_logic", test_size_validation_logic),
    ]
    
    print("Running standard tests...")
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✓ {test_name} passed")
        except Exception as e:
            print(f"✗ {test_name} failed: {e}")
            traceback.print_exc()
    
    print("\nRunning property-based tests...")
    for test_name, test_func in hypothesis_tests:
        try:
            # Run the hypothesis test
            test_func()
            print(f"✓ {test_name} passed")
        except Exception as e:
            print(f"✗ {test_name} failed")
            print(f"Error: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    run_tests()