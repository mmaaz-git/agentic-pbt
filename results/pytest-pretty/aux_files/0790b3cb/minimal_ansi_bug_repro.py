#!/usr/bin/env python3
"""Minimal reproduction of ANSI escape regex bug in pytest-pretty"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pytest-pretty_env/lib/python3.13/site-packages')
import pytest_pretty

# The regex fails to remove several ANSI escape sequences
test_sequences = [
    '\x1b',    # Lone ESC - could appear in truncated output
    '\x1bM',   # Reverse line feed - legitimate ANSI sequence
    '\x1b7',   # Save cursor position - legitimate ANSI sequence
]

for seq in test_sequences:
    cleaned = pytest_pretty.ansi_escape.sub('', seq)
    if '\x1b' in cleaned:
        print(f"Bug: ESC not removed from {repr(seq)} -> {repr(cleaned)}")

# This causes issues when parsing output with these sequences
from unittest.mock import Mock

mock_result = Mock()
mock_result.outlines = [
    'Test output',
    'Results (1.00s):',
    '\x1bM       10 passed',  # ESC M (reverse line feed) before stats
]

parseoutcomes = pytest_pretty.create_new_parseoutcomes(mock_result)
result = parseoutcomes()
print(f"\nParsing issue: Got {result}, expected {{'passed': 10}}")