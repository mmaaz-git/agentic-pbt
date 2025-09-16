#!/usr/bin/env python3
"""Investigate exact conditions for WrappedJoin bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

import fire.formatting as formatting

print("=== Investigating exact trigger conditions for WrappedJoin bug ===")
print()

# Test different scenarios
test_cases = [
    # (items, width, description)
    (['x' * 10], 5, "Single item longer than width"),
    (['x' * 10], 10, "Single item equal to width"),
    (['x' * 10], 11, "Single item just under width"),
    (['x' * 10], 12, "Single item fits with separator"),
    (['x' * 50, 'y' * 50], 20, "Two long items"),
    (['x' * 100], 10, "Very long single item"),
    (['x' * 100], 100, "Long item equal to width"),
    (['x' * 100], 101, "Long item just under width"),
]

separator = ' | '

for items, width, description in test_cases:
    result = formatting.WrappedJoin(items, separator, width)
    has_empty_first = result[0] == ''
    
    print(f"{description}:")
    print(f"  Items: {[f'{item[0]}*{len(item)}' for item in items]}")
    print(f"  Width: {width}")
    print(f"  Result lines: {len(result)}")
    print(f"  First line: {repr(result[0][:50])}..." if len(result[0]) > 50 else f"  First line: {repr(result[0])}")
    if has_empty_first:
        print(f"  >>> BUG: Empty first line!")
    print()

print("=== Analysis ===")
print("The bug occurs when the LAST item in the loop causes current_line to be")
print("appended to lines, and then the final lines.append(current_line) adds an")
print("empty string because current_line was reset.")
print()

# Let's trace through the code logic
print("=== Tracing WrappedJoin logic ===")
items = ['x' * 100]
width = 10
separator = ' | '

lines = []
current_line = ''
for index, item in enumerate(items):
    is_final_item = index == len(items) - 1
    print(f"Processing item {index}: '{item[:10]}...' (final={is_final_item})")
    print(f"  current_line before: '{current_line}'")
    
    if is_final_item:
        if len(current_line) + len(item) <= width:
            current_line += item
            print(f"  -> Added to current_line")
        else:
            lines.append(current_line.rstrip())
            print(f"  -> Appended '{current_line}' to lines")
            current_line = item
            print(f"  -> Reset current_line to item")
    else:
        if len(current_line) + len(item) + len(separator) <= width:
            current_line += item + separator
            print(f"  -> Added to current_line with separator")
        else:
            lines.append(current_line.rstrip())
            print(f"  -> Appended '{current_line}' to lines")
            current_line = item + separator
            print(f"  -> Reset current_line to item + separator")
    
    print(f"  current_line after: '{current_line[:20]}...' if len > 20 else '{current_line}'")
    print()

lines.append(current_line)
print(f"Final append of current_line: '{current_line[:20]}...' if len > 20 else '{current_line}'")
print(f"Result: {len(lines)} lines")
print(f"First line: '{lines[0]}'")
print()

print("=== Bug Explanation ===")
print("When the single item is too long for the width:")
print("1. is_final_item is True")
print("2. current_line is empty ('')")  
print("3. len('') + len(long_item) > width, so we append current_line ('') to lines")
print("4. We set current_line = item")
print("5. After the loop, we append current_line (the long item) to lines")
print("6. Result: ['', 'long_item']")
print()
print("This is a genuine bug that produces an unwanted empty first line.")