#!/usr/bin/env python3
"""Minimal reproduction of Tags.parse() bug"""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages")

from fixit.ftypes import Tags

# This causes an IndexError
try:
    result = Tags.parse(" ")
    print(f"Result: {result}")
except IndexError as e:
    print(f"IndexError: {e}")
    print("Bug confirmed: Tags.parse() crashes on whitespace-only input")

# This also fails
try:
    result = Tags.parse("  \t  ")
    print(f"Result: {result}")
except IndexError as e:
    print(f"IndexError: {e}")
    print("Bug confirmed: Tags.parse() crashes on whitespace-only input with tabs")

# Edge case with comma and whitespace
try:
    result = Tags.parse(" , ")
    print(f"Result: {result}")
except IndexError as e:
    print(f"IndexError: {e}")
    print("Bug confirmed: Tags.parse() crashes on comma with only whitespace")