#!/usr/bin/env python3
"""Minimal reproduction of LineMatcher bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/esp-idf-monitor_env/lib/python3.13/site-packages')

from esp_idf_monitor.base.line_matcher import LineMatcher

# The bug: LineMatcher incorrectly handles filter strings when using tags with colons
# The test discovered this through generating a tag with value ':'

# When we try to create a filter string with a tag containing ':', it causes issues
tag = ':'  # Tag contains colon
level = 'V'

# This creates a filter string "::V" which LineMatcher cannot parse
filter_str = f"{tag}:{level}"
print(f"Filter string: {filter_str}")

try:
    matcher = LineMatcher(filter_str)
    print("SUCCESS: LineMatcher created")
except ValueError as e:
    print(f"ERROR: {e}")

# The issue is in line_matcher.py around line 36-48:
# The code splits by ':' and expects at most 2 parts,
# but doesn't handle the case where the tag itself contains ':'

# Another problematic case - empty tag
filter_str2 = ":V"
print(f"\nFilter string: {filter_str2}")
try:
    matcher = LineMatcher(filter_str2)
    print("SUCCESS: LineMatcher created")
except ValueError as e:
    print(f"ERROR: {e}")