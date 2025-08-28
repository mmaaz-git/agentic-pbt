#!/usr/bin/env python3
"""Minimal reproduction of the _join_lines inconsistency bug."""

import sys
sys.path.append('/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
import fire.docstrings as docstrings

# Bug: Inconsistent handling of empty content in sections
docstring1 = """Function summary.

Returns:
"""

docstring2 = """Function summary.

Returns:
    
"""

docstring3 = """Function summary.

Returns:
     
    
"""

result1 = docstrings.parse(docstring1)
result2 = docstrings.parse(docstring2)  
result3 = docstrings.parse(docstring3)

print("Bug: Empty Returns sections produce '' instead of None")
print(f"docstring1 returns: {result1.returns!r} (expected: None)")
print(f"docstring2 returns: {result2.returns!r} (expected: None)")
print(f"docstring3 returns: {result3.returns!r} (expected: None)")

# The root cause is in _join_lines function
print("\nRoot cause in _join_lines:")
print(f"_join_lines([]) = {docstrings._join_lines([])!r}")
print(f"_join_lines(['']) = {docstrings._join_lines([''])!r}")  
print(f"_join_lines([' ']) = {docstrings._join_lines([' '])!r}")

# This creates API inconsistency
docstring_no_section = "Just a summary."
docstring_empty_section = "Summary.\n\nReturns:\n   "

result_no = docstrings.parse(docstring_no_section)
result_empty = docstrings.parse(docstring_empty_section)

print("\nAPI inconsistency:")
print(f"No Returns section: returns = {result_no.returns!r}")
print(f"Empty Returns section: returns = {result_empty.returns!r}")
print("These should both be None for consistency!")