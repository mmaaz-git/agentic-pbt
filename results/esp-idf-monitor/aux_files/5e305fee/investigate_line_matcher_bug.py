#!/usr/bin/env python3
"""Investigate the LineMatcher bug found by Hypothesis"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/esp-idf-monitor_env/lib/python3.13/site-packages')

from esp_idf_monitor.base.line_matcher import LineMatcher

# Reproduce the failing case
def investigate_bug():
    print("=== Investigating LineMatcher Bug ===\n")
    
    # Test case that failed
    tag = '0'
    level = 'E'
    line_level = 'E'
    
    filter_str = f"{tag}:{level}"
    matcher = LineMatcher(filter_str)
    
    # Create test line
    test_line = f"{line_level} ({tag}): Test message"
    
    print(f"Filter string: {filter_str}")
    print(f"Test line: {test_line}")
    print(f"Matcher._dict: {matcher._dict}")
    
    # Test the match
    result = matcher.match(test_line)
    print(f"Match result: {result}")
    print(f"Expected: True (E level filter should match E level line)")
    
    # Let's also test with the regex directly
    import re
    pattern = matcher._re
    match_obj = pattern.search(test_line)
    if match_obj:
        print(f"\nRegex matched!")
        print(f"Groups: {match_obj.groups()}")
        print(f"Group 1 (level): {match_obj.group(1)}")
        print(f"Group 2 (tag): {match_obj.group(2)}")
    else:
        print(f"\nRegex did NOT match the line")
    
    # Let's try different test lines to understand the pattern
    print("\n=== Testing different line formats ===")
    test_lines = [
        "E (0): Test message",           # Original failing case
        "E (123) 0: Test message",        # With timestamp
        "E 0: Test message",              # Without parentheses
        "E (timestamp) 0: Test message",  # With timestamp in parentheses
    ]
    
    for line in test_lines:
        match_obj = pattern.search(line)
        result = matcher.match(line)
        print(f"\nLine: {line}")
        print(f"  Regex match: {bool(match_obj)}")
        if match_obj:
            print(f"  Groups: {match_obj.groups()}")
        print(f"  Match result: {result}")
    
    # Let's check the regex pattern itself
    print(f"\n=== Regex Pattern ===")
    print(f"Pattern: {pattern.pattern}")
    
    # Test with actual ESP log format
    print("\n=== Testing actual ESP log format ===")
    esp_lines = [
        "E (123) wifi: Connection failed",
        "I (456) app_main: Starting application",
        "W (789) heap: Low memory warning",
        "D (012) mqtt: Sending message",
        "V (345) sys: Verbose debug info",
    ]
    
    matcher_all = LineMatcher("*:V")  # Should match everything
    matcher_error = LineMatcher("*:E")  # Should match only errors
    
    for line in esp_lines:
        match_all = matcher_all.match(line)
        match_error = matcher_error.match(line)
        print(f"\nLine: {line}")
        print(f"  Match with *:V filter: {match_all}")
        print(f"  Match with *:E filter: {match_error}")
        
        # Check what the regex extracts
        match_obj = matcher_all._re.search(line)
        if match_obj:
            print(f"  Extracted - Level: '{match_obj.group(1)}', Tag: '{match_obj.group(2)}'")

if __name__ == '__main__':
    investigate_bug()