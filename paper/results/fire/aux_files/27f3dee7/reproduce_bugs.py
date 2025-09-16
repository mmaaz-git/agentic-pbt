"""Minimal reproductions for discovered bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from fire import helptext
from fire import formatting

print("Bug 1: _GetShortFlags crashes on empty string")
print("=" * 50)
try:
    result = helptext._GetShortFlags([''])
    print(f"Result: {result}")
except IndexError as e:
    print(f"ERROR: {e}")
    print("This crashes when the list contains an empty string")

print("\n\nBug 2: EllipsisTruncate doesn't respect line_length when too small")
print("=" * 50)
text = '00'
available_space = 0
line_length = 1
result = formatting.EllipsisTruncate(text, available_space, line_length)
print(f"Text: '{text}'")
print(f"Available space: {available_space}, Line length: {line_length}")
print(f"Result: '{result}' (length: {len(result)})")
print(f"Expected: Result length <= {line_length}")
print(f"VIOLATION: {len(result)} > {line_length}")

print("\n\nBug 3: EllipsisMiddleTruncate doesn't respect line_length when too small")
print("=" * 50)
text = '0'
available_space = 0
line_length = 1
result = formatting.EllipsisMiddleTruncate(text, available_space, line_length)
print(f"Text: '{text}'")
print(f"Available space: {available_space}, Line length: {line_length}")
print(f"Result: '{result}' (length: {len(result)})")
print(f"Expected: Result length <= {line_length}")
print(f"VIOLATION: {len(result)} > {line_length}")

print("\n\nBug 4: WrappedJoin doesn't handle items longer than width")
print("=" * 50)
items = ['00000000000']
separator = ' | '
width = 10
lines = formatting.WrappedJoin(items, separator, width)
print(f"Items: {items}")
print(f"Width constraint: {width}")
print(f"Result lines: {lines}")
for line in lines:
    print(f"  Line: '{line}' (length: {len(line)})")
    if len(line) > width:
        print(f"  VIOLATION: {len(line)} > {width}")