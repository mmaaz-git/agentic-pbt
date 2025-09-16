#!/usr/bin/env python3
"""Minimal reproductions of bugs found in esp_idf_monitor"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/esp-idf-monitor_env/lib/python3.13/site-packages')

from esp_idf_monitor.base.line_matcher import LineMatcher
from esp_idf_monitor.base.output_helpers import add_common_prefix

print("=== BUG 1: LineMatcher fails with tags containing spaces ===\n")

# Create a filter for a tag with leading space
filter_str = " wifi:E"  # Tag with leading space
matcher = LineMatcher(filter_str)

# This log line should match the filter
log_line = "E (1234)  wifi: Connection error"

# Test the match
result = matcher.match(log_line)
print(f"Filter: '{filter_str}'")
print(f"Log line: '{log_line}'")
print(f"Match result: {result}")
print(f"Expected: True")
print("\nThe bug: Filter parsing strips spaces from tags, but matching preserves them.")

print("\n=== BUG 2: add_common_prefix mishandles carriage returns ===\n")

# Message with carriage return
message = "\r0"
prefix = ">>>"

result = add_common_prefix(message, prefix=prefix)

print(f"Input message: {repr(message)}")
print(f"Prefix: {repr(prefix)}")
print(f"Result: {repr(result)}")
print(f"Expected: {repr('>>> \\r0')} or similar")
print("\nThe bug: When splitlines() encounters \\r, it treats subsequent")
print("characters as a new line, causing incorrect prefix placement.")