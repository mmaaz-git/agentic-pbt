#!/usr/bin/env python3
"""Test to verify type annotation bug in print_result."""

import sys
from pathlib import Path

sys.path.insert(0, "/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages")

from fixit.api import print_result
from fixit.ftypes import Result
import io
import contextlib

# Test the actual return type
print("Testing print_result return type...")
print("=" * 60)

# Test 1: Clean result
clean_result = Result(path=Path("test.py"), violation=None, error=None)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    return_value = print_result(clean_result)

print(f"Clean result return value: {return_value}")
print(f"Type: {type(return_value)}")
print(f"Is bool? {isinstance(return_value, bool)}")
print(f"Is int? {isinstance(return_value, int)}")

# In Python, bool is a subclass of int, but the function is annotated as -> int
# while it semantically returns bool values (True/False)
print("\nNote: In Python, bool is a subclass of int, so isinstance(True, int) = True")
print("However, the function signature says '-> int' but docstring and implementation")
print("clearly indicate it returns boolean values (True/False) for semantic meaning.")

# Check function annotations
print("\n" + "=" * 60)
print("Function annotation check:")
print(f"print_result.__annotations__ = {print_result.__annotations__}")

# The bug is that the type hint says -> int but the docstring and usage pattern
# indicate it should be -> bool
print("\n" + "=" * 60)
print("BUG FOUND:")
print("- Type annotation: -> int (line 27)")
print("- Docstring: 'Returns ``True`` if the result is \"dirty\"' (line 34)") 
print("- Implementation: returns True/False (lines 56, 63, 67)")
print("\nThe type annotation should be '-> bool' to match the documented behavior.")