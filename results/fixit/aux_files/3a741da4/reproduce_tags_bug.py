#!/usr/bin/env python3
"""Minimal reproduction of the Tags.parse() bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

from fixit.ftypes import Tags

# Bug 1: Single comma causes IndexError
try:
    result = Tags.parse(",")
    print(f"Parsed ',' successfully: {result}")
except IndexError as e:
    print(f"Bug: Tags.parse(',') raises IndexError: {e}")

# Bug 2: Whitespace string causes IndexError  
try:
    result = Tags.parse("   ")
    print(f"Parsed '   ' successfully: {result}")
except IndexError as e:
    print(f"Bug: Tags.parse('   ') raises IndexError: {e}")

# Bug 3: Multiple commas
try:
    result = Tags.parse(",,")
    print(f"Parsed ',,' successfully: {result}")
except IndexError as e:
    print(f"Bug: Tags.parse(',,') raises IndexError: {e}")

# Bug 4: Comma with spaces
try:
    result = Tags.parse(" , ")
    print(f"Parsed ' , ' successfully: {result}")
except IndexError as e:
    print(f"Bug: Tags.parse(' , ') raises IndexError: {e}")