#!/usr/bin/env python3
"""Minimal reproduction of the octal formatting bug in ArgFormatter."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/esp-idf-monitor_env/lib/python3.13/site-packages')

from esp_idf_monitor.base.binlog import ArgFormatter

# Test the bug
formatter = ArgFormatter()

# Test with value 0
result = formatter.c_format("%#o", [0])
print(f"formatter.c_format('%#o', [0]) = '{result}'")
print(f"Expected: '0'")
print(f"Bug confirmed: {result != '0'}")
print()

# Test with other values to understand the pattern
test_values = [0, 1, 7, 8, 15, 16]
for value in test_values:
    result = formatter.c_format("%#o", [value])
    expected_python = f"{value:#o}" if value != 0 else "0"
    expected_c = f"0{value:o}" if value != 0 else "0"
    print(f"Value {value}: result='{result}', Python format='{expected_python}', C expected='{expected_c}'")