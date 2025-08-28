#!/usr/bin/env python3
"""
Reproduce the infinite loop bug in split_string_literal.
"""

import Cython.Compiler.StringEncoding as SE

# This should trigger the bug
print("Testing split_string_literal with limit=0...")
print("This will hang indefinitely!")

# The bug: split_string_literal enters infinite loop with limit <= 0
result = SE.split_string_literal("test", 0)
print(f"Result: {result}")  # This line will never be reached