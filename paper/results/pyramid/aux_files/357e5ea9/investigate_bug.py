#!/usr/bin/env python3
"""Investigate the JSONP callback validation bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import re
import pyramid.renderers as renderers

# The failing callback
callback = "A0"

# Test with the regex directly
pattern = renderers.JSONP_VALID_CALLBACK
print(f"Pattern: {pattern.pattern}")
print(f"Pattern flags: {pattern.flags}")
print(f"Testing callback: '{callback}'")

match = pattern.match(callback)
print(f"Direct regex match result: {match}")

if match:
    print(f"Match groups: {match.groups()}")
    print(f"Matched string: '{match.group()}'")

# Let's break down what the regex should match
print("\nRegex breakdown:")
print("^[$a-z_]  - Start with $, letter (case insensitive), or _")
print("[$0-9a-z_\.\[\]]+  - One or more: $, digit, letter, _, ., [, ]")
print("[^.]$  - End with anything except a dot")

# Test A0 step by step
print(f"\n'A' matches ^[$a-z_]: {bool(re.match(r'^[$a-z_]', 'A', re.I))}")
print(f"'0' matches [$0-9a-z_\.\[\]]: {bool(re.match(r'[$0-9a-z_\.\[\]]', '0', re.I))}")
print(f"'0' is not '.': {('0' != '.')}")

# Let's see what the actual pattern requires
print("\nActual pattern requirements:")
print(f"Pattern requires at least 3 characters? {'+' in pattern.pattern}")

# Check the actual length requirement
print(f"\nChecking if the regex requires minimum length...")
print(f"'A' matches: {bool(pattern.match('A'))}")
print(f"'AB' matches: {bool(pattern.match('AB'))}")
print(f"'A0' matches: {bool(pattern.match('A0'))}")
print(f"'ABC' matches: {bool(pattern.match('ABC'))}")
print(f"'_0' matches: {bool(pattern.match('_0'))}")
print(f"'$0' matches: {bool(pattern.match('$0'))}")

# Wait, let me look at the pattern more carefully
print("\nCareful analysis of pattern: ^[$a-z_][$0-9a-z_\.\[\]]+[^.]$")
print("This means:")
print("1. Start with [$a-z_]")
print("2. Then ONE OR MORE of [$0-9a-z_\.\[\]]")
print("3. Then end with [^.] (a single character that is not a dot)")
print("\nSo minimum length is 3 characters!")

print(f"\n'A0' has length {len('A0')}, so it can't match because:")
print("- First char 'A' matches ^[$a-z_]")
print("- Second char '0' matches [$0-9a-z_\.\[\]]+")
print("- But there's no third character to match [^.]")

# Let's test with 3-character strings
print("\nTesting 3-character callbacks:")
test_callbacks = ["A00", "A0B", "ABC", "_0a", "$0x"]
for cb in test_callbacks:
    print(f"'{cb}' matches: {bool(pattern.match(cb))}")