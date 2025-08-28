#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/mdxpy_env/lib/python3.13/site-packages')

from mdxpy.mdx import DescFlag

# The DescFlag enum has a member SELF_AND_AFTER
# It should parse "selfandafter" (without underscores) correctly
# since the _missing_ method does value.replace(" ", "").lower()

test_values = [
    "SELF_AND_AFTER",  # This should work
    "self_and_after",  # This should work  
    "selfandafter",    # This should work but doesn't
]

for val in test_values:
    try:
        result = DescFlag._missing_(val)
        print(f"✓ '{val}' -> {result}")
    except ValueError as e:
        print(f"✗ '{val}' -> ERROR: {e}")

# The issue is that the enum comparison doesn't handle underscores properly
# When comparing member.name.lower() == value.replace(" ", "").lower()
# "self_and_after".lower() == "selfandafter" returns False