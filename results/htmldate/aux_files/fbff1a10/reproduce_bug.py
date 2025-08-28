#!/usr/bin/env python3
"""Minimal reproduction of the bug in correct_year function."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from htmldate.extractors import correct_year

# Test with negative year
print(f"correct_year(-1) = {correct_year(-1)}")
print(f"Expected: -1")
print(f"Actual: {correct_year(-1)}")
print()

# Let's test a few more negative values
for year in [-1, -10, -50, -99]:
    result = correct_year(year)
    print(f"correct_year({year}) = {result}")
print()

# According to the function logic:
# if year < 100:
#     year += 1900 if year >= 90 else 2000
# 
# For year = -1:
# -1 < 100 is True
# -1 >= 90 is False
# So it does: -1 + 2000 = 1999