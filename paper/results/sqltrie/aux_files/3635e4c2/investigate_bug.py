#!/usr/bin/env python3
"""Further investigation of LineMatcher bug with edge cases"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/esp-idf-monitor_env/lib/python3.13/site-packages')

from esp_idf_monitor.base.line_matcher import LineMatcher

print("Testing various edge cases for LineMatcher filter parsing:\n")

# Test cases that might cause issues
test_cases = [
    ("::V", "Tag with single colon"),
    (":V", "Empty tag with level"),
    ("tag::V", "Tag with colon at end"),
    ("ta:g:V", "Tag with colon in middle"),
    ("tag::", "Tag with empty level after double colon"),
    (":::V", "Triple colon"),
    ("tag1:V tag2::E", "Multiple filters with colon issues"),
]

for filter_str, description in test_cases:
    print(f"{description}: '{filter_str}'")
    try:
        matcher = LineMatcher(filter_str)
        print(f"  ✓ SUCCESS: Created matcher with dict: {matcher._dict}")
    except ValueError as e:
        print(f"  ✗ ERROR: {e}")
    print()

# Now test what happens when we have lines with colons in tags
print("\nTesting line matching with colons in tags:\n")

# Create a simple matcher
matcher = LineMatcher("*:V")  # Allow all verbose

# Test lines with various formats
test_lines = [
    "V (normal_tag): message",
    "V (tag:with:colon): message",  # Tag contains colons
    "V (:): message",  # Tag is just a colon
    "V (::): message",  # Tag is double colon
]

for line in test_lines:
    print(f"Line: '{line}'")
    try:
        result = matcher.match(line)
        print(f"  Match result: {result}")
    except Exception as e:
        print(f"  ERROR: {e}")
    print()