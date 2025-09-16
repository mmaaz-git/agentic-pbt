"""Minimal reproductions of bugs found in fire.formatting module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
import fire.formatting as fmt


print("=== BUG: WrappedJoin strips trailing whitespace from separator ===")
print()

# Minimal reproduction
items = ['foo', 'bar', 'baz']
separator = ' | '  # Has trailing space
width = 10  # Forces wrapping

result = fmt.WrappedJoin(items, separator, width)

print(f"Input items: {items}")
print(f"Separator: {repr(separator)}")
print(f"Width: {width}")
print(f"Result: {result}")
print()

# The bug: the separator ' | ' becomes ' |' (trailing space removed)
print("Expected behavior: Separator should remain ' | ' between items")
print("Actual behavior: Separator becomes ' |' (trailing space removed)")
print()

# Show the issue
for i, line in enumerate(result):
    print(f"Line {i}: {repr(line)}")
    if ' |' in line and not ' | ' in line:
        print(f"  ^^^ Bug: separator ' | ' was stripped to ' |'")

print()
print("Root cause: lines 53 and 59 in formatting.py use rstrip() which removes")
print("trailing whitespace from lines, inadvertently stripping whitespace from separators.")