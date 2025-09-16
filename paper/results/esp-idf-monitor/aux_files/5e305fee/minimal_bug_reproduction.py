#!/usr/bin/env python3
"""Minimal reproduction of the LineMatcher bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/esp-idf-monitor_env/lib/python3.13/site-packages')

from esp_idf_monitor.base.line_matcher import LineMatcher

# Bug reproduction: parentheses in test confuse the regex
def reproduce_bug():
    print("=== Bug: LineMatcher incorrectly parses tags when parentheses are involved ===\n")
    
    # Create a filter for tag "mytag" at error level
    matcher = LineMatcher("mytag:E")
    print(f"Filter: mytag:E")
    print(f"Matcher dictionary: {matcher._dict}")
    print()
    
    # Test Case 1: Standard ESP-IDF log format (should work correctly)
    line1 = "E (12345) mytag: Error message"
    result1 = matcher.match(line1)
    print(f"Line 1: {line1}")
    print(f"  Expected: True (mytag at E level should match)")
    print(f"  Actual: {result1}")
    print()
    
    # Test Case 2: Non-standard format that reveals the bug
    # If someone mistakenly formats like this (tag in parentheses), the regex fails
    line2 = "E (mytag): Error message"
    result2 = matcher.match(line2)
    print(f"Line 2: {line2}")
    print(f"  Expected: True (mytag at E level should match)")
    print(f"  Actual: {result2}")
    print()
    
    # What the regex actually extracts
    import re
    match1 = matcher._re.search(line1)
    match2 = matcher._re.search(line2)
    
    print("What the regex extracts:")
    if match1:
        print(f"  Line 1 - Level: '{match1.group(1)}', Tag: '{match1.group(2)}'")
    if match2:
        print(f"  Line 2 - Level: '{match2.group(1)}', Tag: '{match2.group(2)}'")
    
    print("\n=== Analysis ===")
    print("The bug occurs because the regex pattern:")
    print(f"  {matcher._re.pattern}")
    print("\nAssumes the format: LEVEL (optional_timestamp) TAG: message")
    print("But when the tag itself is in parentheses like 'E (mytag):', ")
    print("it incorrectly captures '(mytag)' as the tag instead of 'mytag'.")
    print("\nThis causes the filter lookup to fail since the dictionary has 'mytag'")
    print("but the regex extracts '(mytag)'.")

if __name__ == '__main__':
    reproduce_bug()