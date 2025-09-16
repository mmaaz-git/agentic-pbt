#!/usr/bin/env python3
"""Minimal reproduction of whitespace parsing bug in fire.parser."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from fire import parser

# Demonstrate the bug: leading whitespace breaks parsing
print("Bug: Leading whitespace causes DefaultParseValue to fail parsing\n")

# Example 1: Integer parsing
value_without_space = parser.DefaultParseValue('42')
value_with_space = parser.DefaultParseValue(' 42')

print(f"parser.DefaultParseValue('42')  = {repr(value_without_space)} (type: {type(value_without_space).__name__})")
print(f"parser.DefaultParseValue(' 42') = {repr(value_with_space)} (type: {type(value_with_space).__name__})")
print(f"Expected: Both should return 42 (int)")
print(f"Actual: Leading space causes string return instead of parsing\n")

# Example 2: Boolean parsing
bool_without_space = parser.DefaultParseValue('True')
bool_with_space = parser.DefaultParseValue(' True')

print(f"parser.DefaultParseValue('True')  = {repr(bool_without_space)} (type: {type(bool_without_space).__name__})")
print(f"parser.DefaultParseValue(' True') = {repr(bool_with_space)} (type: {type(bool_with_space).__name__})")
print(f"Expected: Both should return True (bool)")
print(f"Actual: Leading space causes string return\n")

# Example 3: List parsing
list_without_space = parser.DefaultParseValue('[1, 2, 3]')
list_with_space = parser.DefaultParseValue(' [1, 2, 3]')

print(f"parser.DefaultParseValue('[1, 2, 3]')  = {repr(list_without_space)}")
print(f"parser.DefaultParseValue(' [1, 2, 3]') = {repr(list_with_space)}")
print(f"Expected: Both should return [1, 2, 3] (list)")
print(f"Actual: Leading space causes string return\n")

# This is problematic for CLI users who might accidentally include spaces
print("Impact: Users typing commands with accidental leading spaces will get unexpected behavior")
print("Example: 'fire script.py function  42' vs 'fire script.py function 42'")