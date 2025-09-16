#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-pandas_env/lib/python3.13/site-packages')

import pandas as pd
from dagster_pandas.constraints import StrictColumnsConstraint

print("Bug Reproduction: StrictColumnsConstraint fails to detect missing columns")
print("=" * 70)

# Create a constraint that expects columns ['a', 'b', 'c'] without ordering
constraint = StrictColumnsConstraint(['a', 'b', 'c'], enforce_ordering=False)

# Create a DataFrame missing column 'c'
df = pd.DataFrame(columns=['a', 'b'])

print(f"Expected columns: {['a', 'b', 'c']}")
print(f"DataFrame columns: {list(df.columns)}")
print(f"Missing column: 'c'")
print()

try:
    constraint.validate(df)
    print("BUG CONFIRMED: validate() passed despite missing column 'c'")
    print("The constraint should have raised DataFrameConstraintViolationException")
except Exception as e:
    print(f"Correctly raised exception: {e}")

print("\n" + "=" * 70)
print("Root cause analysis:")
print("Looking at the validate() method in StrictColumnsConstraint...")
print()

# Let's trace through the logic
columns_received = list(df.columns)  # ['a', 'b']
strict_column_list = ['a', 'b', 'c']
enforce_ordering = False

print(f"columns_received = {columns_received}")
print(f"strict_column_list = {strict_column_list}")
print(f"enforce_ordering = {enforce_ordering}")
print()

# The code at line 329-334 in constraints.py does:
print("The validation loop (lines 329-334) only checks:")
print("  for column in columns_received:")
print("      if column not in self.strict_column_list:")
print("          raise exception")
print()
print("This only validates that received columns are in the allowed list,")
print("but DOES NOT check that all required columns are present!")
print()
print("When enforce_ordering=False, it never checks if strict_column_list")
print("is a subset of columns_received, only the reverse.")