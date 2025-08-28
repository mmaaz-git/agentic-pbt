#!/usr/bin/env python3
"""Property-based test that discovered the LineMatcher bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/esp-idf-monitor_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
from esp_idf_monitor.base.line_matcher import LineMatcher

@given(
    st.text(min_size=1, max_size=20),  # tag
    st.sampled_from(['N', 'E', 'W', 'I', 'D', 'V', '*', ''])  # level
)
def test_line_matcher_filter_construction(tag, level):
    """Property: Any valid tag and level should create a valid filter string"""
    # Build a filter string from tag and level
    if level:
        filter_str = f"{tag}:{level}"
    else:
        filter_str = tag
    
    # This should not raise an exception for any tag/level combination
    # But it does when tag contains ':'
    try:
        matcher = LineMatcher(filter_str)
        assert isinstance(matcher._dict, dict)
    except ValueError as e:
        # Bug found: LineMatcher fails when tag contains ':'
        if ':' in tag:
            # This is the bug we found
            print(f"BUG: LineMatcher fails with tag='{tag}', level='{level}'")
            print(f"  Filter string: '{filter_str}'")
            print(f"  Error: {e}")
            raise

if __name__ == '__main__':
    # Run the test to demonstrate the bug
    test_line_matcher_filter_construction()