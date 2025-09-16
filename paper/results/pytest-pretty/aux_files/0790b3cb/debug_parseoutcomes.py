import re
import sys
from unittest.mock import Mock
from itertools import dropwhile

sys.path.insert(0, '/root/hypothesis-llm/envs/pytest-pretty_env/lib/python3.13/site-packages')
import pytest_pretty

# Test with the exact sequence from the failing test
print("Testing with the exact failing case:")
mock_result = Mock()
mock_result.outlines = [
    'Some initial output', 
    'Results (1.23s):', 
    'next line',  # <-- This is the problem
    '        0 A',
    'Some trailing output'
]

print("Outlines:")
for i, line in enumerate(mock_result.outlines):
    print(f"  {i}: '{line}'")

parseoutcomes = pytest_pretty.create_new_parseoutcomes(mock_result)
result = parseoutcomes()
print(f"\nParsed result: {result}")
print(f"Expected: {{'A': 0}}")

# Let's trace through manually
print("\nManual trace:")
lines_with_stats = dropwhile(lambda x: 'Results' not in x, mock_result.outlines)
print("After dropwhile, next() to skip Results line...")
next(lines_with_stats)  # This skips the Results line

res = {}
for i, line in enumerate(lines_with_stats):
    print(f"Processing line {i}: '{line}'")
    cleaned_line = pytest_pretty.ansi_escape.sub('', line).strip()
    print(f"  Cleaned: '{cleaned_line}'")
    match = pytest_pretty.stat_re.match(cleaned_line)
    print(f"  Match: {match}")
    if match is None:
        print("  No match, breaking")
        break
    res[match.group(2)] = int(match.group(1))

print(f"Final result: {res}")