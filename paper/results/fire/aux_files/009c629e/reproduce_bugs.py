#!/usr/bin/env python3
"""Minimal reproductions of bugs found in fire.helptext and fire.formatting."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

import fire.helptext as helptext
import fire.formatting as formatting

print("=== Bug 1: _CreateItem with newline in name ===")
# When name contains a newline, the indentation logic fails
name = '\n0'
description = '0'
indent = 1

result = helptext._CreateItem(name, description, indent)
print(f"name: {repr(name)}")
print(f"description: {repr(description)}")
print(f"indent: {indent}")
print(f"result: {repr(result)}")
print(f"result lines: {result.split(chr(10))}")

# Expected: Description should be indented
# Actual: The second line (which is '0' from the name) is not the description
# The actual description appears on the third line
print()

print("=== Bug 2: WrappedJoin with item longer than width ===")
# When an item is longer than the width, WrappedJoin produces unexpected output
long_item = '0' * 100
width = 10
items = [long_item]

result_lines = formatting.WrappedJoin(items, ' | ', width)
print(f"long_item length: {len(long_item)}")
print(f"width: {width}")
print(f"result_lines: {result_lines}")
print(f"first line: {repr(result_lines[0])}")
print(f"long_item in first line: {long_item in result_lines[0]}")

# Expected: The long item should still appear in the output (perhaps on its own line)
# Actual: First line is empty when item is longer than width
print()

print("=== Bug 2b: WrappedJoin loses content ===")
# Testing if the item appears anywhere in the output
joined = ''.join(result_lines)
print(f"long_item in joined result: {long_item in joined}")
print(f"joined result: {repr(joined)}")

# The item is lost entirely!
print()

print("=== Bug 3: WrappedJoin with multiple long items ===")
items = ['a' * 50, 'b' * 50, 'c' * 50]
width = 20
result_lines = formatting.WrappedJoin(items, ' | ', width)
print(f"items: {[len(item) for item in items]} chars each")
print(f"width: {width}")
print(f"result_lines: {result_lines}")

# Check if all items appear
for i, item in enumerate(items):
    joined = ''.join(result_lines)
    if item in joined:
        print(f"Item {i} ({item[0]}*{len(item)}) found in output")
    else:
        print(f"Item {i} ({item[0]}*{len(item)}) MISSING from output!")