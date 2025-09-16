import re
import sys
from unittest.mock import Mock

sys.path.insert(0, '/root/hypothesis-llm/envs/pytest-pretty_env/lib/python3.13/site-packages')
import pytest_pretty

# Bug 1: ANSI escape regex doesn't remove lone ESC character
print("Bug 1: Testing ANSI escape removal with lone ESC character")
text = '\x1b'
cleaned = pytest_pretty.ansi_escape.sub('', text)
print(f"Original: {repr(text)}")
print(f"Cleaned: {repr(cleaned)}")
print(f"ESC still present: {'\x1b' in cleaned}")
print()

# Bug 2: parseoutcomes fails when count is 0
print("Bug 2: Testing parseoutcomes with count=0")
mock_result = Mock()
mock_result.outlines = [
    'Initial output',
    'Results (1.23s):',
    '        0 A',
    'trailing'
]
parseoutcomes = pytest_pretty.create_new_parseoutcomes(mock_result)
result = parseoutcomes()
print(f"Input lines: {mock_result.outlines}")
print(f"Parsed result: {result}")
print(f"Expected: {{'A': 0}}")
print()

# Let's debug the parsing
print("Debug: Testing stat_re regex with '0 A'")
line = '0 A'
match = pytest_pretty.stat_re.match(line)
print(f"Line: '{line}'")
print(f"Match: {match}")
if match:
    print(f"Groups: {match.groups()}")

print("\nDebug: Testing what parseoutcomes sees")
mock_result2 = Mock()
mock_result2.outlines = [
    'Initial output',
    'Results (1.23s):',
    '        0 A',
    '        1 B',
    'trailing'
]
parseoutcomes2 = pytest_pretty.create_new_parseoutcomes(mock_result2)

# Let's trace through the function manually
from itertools import dropwhile
lines_with_stats = dropwhile(lambda x: 'Results' not in x, mock_result2.outlines)
next(lines_with_stats)  # drop Results line
res = {}
for i, line in enumerate(lines_with_stats):
    print(f"Processing line {i}: '{line}'")
    cleaned_line = pytest_pretty.ansi_escape.sub('', line).strip()
    print(f"  Cleaned: '{cleaned_line}'")
    match = pytest_pretty.stat_re.match(cleaned_line)
    print(f"  Match: {match}")
    if match:
        print(f"  Groups: {match.groups()}")
        res[match.group(2)] = int(match.group(1))
    else:
        break
print(f"Final result: {res}")