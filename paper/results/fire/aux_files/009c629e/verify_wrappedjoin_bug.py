#!/usr/bin/env python3
"""Verify the WrappedJoin bug affects real usage."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

import fire.helptext as helptext
import fire.formatting as formatting

print("=== Testing WrappedJoin bug in real usage context ===")
print()

# Simulate what happens in _CreateAvailabilityLine with long flag names
header = "optional flags:"
# Some flags with very long names (this could happen with generated code or certain libraries)
items = [
    '--very_long_flag_name_that_exceeds_normal_width',
    '--another_extremely_long_flag_for_configuration',
    '--short'
]

header_indent = 2
items_indent = 25  # This is the default in _CreateAvailabilityLine
line_length = 80  # Default LINE_LENGTH

items_width = line_length - items_indent  # = 55

print(f"items_width: {items_width}")
print(f"Flag lengths: {[len(item) for item in items]}")
print()

# This is what _CreateAvailabilityLine does:
wrapped_lines = formatting.WrappedJoin(items, width=items_width)
print(f"WrappedJoin result:")
for i, line in enumerate(wrapped_lines):
    print(f"  Line {i}: {repr(line)}")
print()

# Join and indent
items_text = '\n'.join(wrapped_lines)
indented_items_text = formatting.Indent(items_text, spaces=items_indent)
indented_header = formatting.Indent(header, spaces=header_indent)

# This is the final output
result = indented_header + indented_items_text[len(indented_header):] + '\n'
print("Final formatted output:")
print(result)
print()

print("=== Issue Analysis ===")
if wrapped_lines[0] == '':
    print("BUG CONFIRMED: First line is empty when first item exceeds width!")
    print("This would create incorrect formatting in help text.")
else:
    print("Bug not triggered in this case")

# Test with realistic but long flag names
print("\n=== Testing with realistic long flags ===")
items = [
    '--enable_experimental_feature_with_long_name',
    '--disable_legacy_compatibility_mode',
    '--max_concurrent_connections_limit'
]

wrapped_lines = formatting.WrappedJoin(items, width=items_width)
print(f"Flag lengths: {[len(item) for item in items]}")
print(f"WrappedJoin result:")
for i, line in enumerate(wrapped_lines):
    print(f"  Line {i}: {repr(line)}")

if wrapped_lines[0] == '':
    print("\nBUG: Empty first line detected!")
    print("This affects real-world usage with moderately long flag names.")