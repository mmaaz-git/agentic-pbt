#!/usr/bin/env python3
"""Investigate the bugs found by Hypothesis"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/esp-idf-monitor_env/lib/python3.13/site-packages')

from esp_idf_monitor.base.line_matcher import LineMatcher
from esp_idf_monitor.base.output_helpers import add_common_prefix

print("=== Bug 1: LineMatcher with leading space in tag ===\n")

# Bug 1: Tag with leading space
tag = ' 0'  # Tag with leading space
level = 'E'

filter_str = f"{tag}:{level}"
print(f"Filter string: '{filter_str}'")

matcher = LineMatcher(filter_str)
print(f"Matcher dictionary: {matcher._dict}")

# Create test line with the tag
test_line = f"E (12345) {tag}: Test message"
print(f"Test line: '{test_line}'")

result = matcher.match(test_line)
print(f"Match result: {result}")
print(f"Expected: True (should match tag ' 0' at E level)")

# Check what the regex extracts
import re
match_obj = matcher._re.search(test_line)
if match_obj:
    print(f"Regex matched - Level: '{match_obj.group(1)}', Tag: '{match_obj.group(2)}'")
else:
    print("Regex did not match")

print("\n=== Bug 2: add_common_prefix with carriage return ===\n")

# Bug 2: Message with carriage return
message = '\r0'
prefix = '0'

print(f"Message: {repr(message)}")
print(f"Prefix: {repr(prefix)}")

result = add_common_prefix(message, prefix=prefix)
print(f"Result: {repr(result)}")
print(f"Expected: '0 \\r0' (prefix should be added before non-empty content)")

# Let's understand what's happening
lines = message.splitlines(keepends=True)
print(f"\nSplitlines with keepends=True: {lines}")
print(f"Number of lines: {len(lines)}")

for i, line in enumerate(lines):
    print(f"Line {i}: {repr(line)}")
    print(f"  Strip result: {repr(line.strip())}")
    print(f"  Is empty after strip: {not line.strip()}")

# Test the actual implementation logic
print("\n=== Understanding the implementation ===")
print("The function uses: message.splitlines(keepends=True)")
print("Then checks: if line.strip()")

# More test cases with different line endings
test_cases = [
    '\r0',      # Carriage return followed by content
    '0\r',      # Content followed by carriage return  
    '\n0',      # Newline followed by content
    '0\n',      # Content followed by newline
    '\r\n0',    # CRLF followed by content
    '0\r\n',    # Content followed by CRLF
]

for msg in test_cases:
    result = add_common_prefix(msg, prefix='PREFIX')
    print(f"\nMessage: {repr(msg)}")
    print(f"Result:  {repr(result)}")