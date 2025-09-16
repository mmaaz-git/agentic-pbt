#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-pandas_env/lib/python3.13/site-packages')

import pandas as pd
from dagster_pandas.constraints import (
    StrictColumnsConstraint,
    RowCountConstraint,
    InRangeColumnConstraint,
    MinValueColumnConstraint,
    MaxValueColumnConstraint,
)
from dagster_pandas.data_frame import create_table_schema_metadata_from_dataframe

print("Testing dagster_pandas properties...")
print("=" * 60)

# Test 1: StrictColumnsConstraint edge case with empty columns
print("\nTest 1: Testing StrictColumnsConstraint with edge cases...")
try:
    # Test with empty column list
    constraint = StrictColumnsConstraint([], enforce_ordering=True)
    df = pd.DataFrame()
    constraint.validate(df)
    print("✓ Empty columns validated correctly")
except Exception as e:
    print(f"✗ Issue with empty columns: {e}")

# Test with missing columns  
try:
    constraint = StrictColumnsConstraint(['a', 'b', 'c'], enforce_ordering=False)
    df = pd.DataFrame(columns=['a', 'b'])  # Missing 'c'
    constraint.validate(df)
    print("✗ BUG: Should have failed for missing column 'c'")
except Exception as e:
    print("✓ Correctly failed for missing column")

# Test 2: RowCountConstraint with negative tolerance
print("\nTest 2: Testing RowCountConstraint with negative tolerance...")
try:
    # The code uses abs() on tolerance, so negative should become positive
    constraint = RowCountConstraint(10, error_tolerance=-5)
    assert constraint.error_tolerance == 5
    print("✓ Negative tolerance correctly converted to positive")
except AssertionError:
    print("✗ BUG: Negative tolerance not handled correctly")

# Test 3: Boundary comparison operators
print("\nTest 3: Testing MinValue/MaxValue boundary conditions...")
try:
    # Test MinValueColumnConstraint with exact boundary
    min_constraint = MinValueColumnConstraint(5.0, ignore_missing_vals=False)
    
    # Test with value exactly at minimum (should pass per docstring: "greater than...inclusive")
    df_exact = pd.DataFrame({'col': [5.0]})
    min_constraint.validate(df_exact, 'col')
    print("✓ MinValue: Exact boundary value passes (inclusive)")
    
    # Test with value below minimum
    df_below = pd.DataFrame({'col': [4.999]})
    try:
        min_constraint.validate(df_below, 'col')
        print("✗ BUG: Value below minimum should fail")
    except:
        print("✓ MinValue: Value below minimum correctly fails")
        
except Exception as e:
    print(f"✗ Unexpected error in MinValue test: {e}")

# Test MaxValueColumnConstraint
try:
    max_constraint = MaxValueColumnConstraint(10.0, ignore_missing_vals=False)
    
    # Test with value exactly at maximum (should pass per docstring: "less than...inclusive")
    df_exact = pd.DataFrame({'col': [10.0]})
    max_constraint.validate(df_exact, 'col')
    print("✓ MaxValue: Exact boundary value passes (inclusive)")
    
    # Test with value above maximum
    df_above = pd.DataFrame({'col': [10.001]})
    try:
        max_constraint.validate(df_above, 'col')
        print("✗ BUG: Value above maximum should fail")
    except:
        print("✓ MaxValue: Value above maximum correctly fails")
        
except Exception as e:
    print(f"✗ Unexpected error in MaxValue test: {e}")

# Test 4: InRangeColumnConstraint comparison logic
print("\nTest 4: Testing InRangeColumnConstraint boundaries...")
try:
    constraint = InRangeColumnConstraint(0, 10, ignore_missing_vals=False)
    
    # Test exact boundaries
    df_min = pd.DataFrame({'col': [0]})
    df_max = pd.DataFrame({'col': [10]})
    
    constraint.validate(df_min, 'col')
    constraint.validate(df_max, 'col')
    print("✓ InRange: Both boundaries inclusive")
    
    # Test outside range
    df_below = pd.DataFrame({'col': [-0.1]})
    df_above = pd.DataFrame({'col': [10.1]})
    
    failed_below = False
    failed_above = False
    
    try:
        constraint.validate(df_below, 'col')
    except:
        failed_below = True
        
    try:
        constraint.validate(df_above, 'col')
    except:
        failed_above = True
        
    if failed_below and failed_above:
        print("✓ InRange: Values outside range correctly fail")
    else:
        print(f"✗ BUG: Outside range validation issue (below_failed={failed_below}, above_failed={failed_above})")
        
except Exception as e:
    print(f"✗ Unexpected error in InRange test: {e}")

# Test 5: Look for comparison operator bug
print("\nTest 5: Investigating comparison operators in constraints...")

# Check MinValueColumnConstraint source for operator
# Line 1025 in constraints.py: invalid = dataframe[column_name] < self.min_value
# This means values LESS THAN min_value are invalid
# So values >= min_value should be valid
# But docstring says "greater than" which is ambiguous about equality

print("Checking MinValueColumnConstraint implementation...")
min_constraint = MinValueColumnConstraint(5, ignore_missing_vals=False)

# Edge case: Check if = is handled correctly
df_equal = pd.DataFrame({'col': [5]})
df_less = pd.DataFrame({'col': [4.99999]})

try:
    min_constraint.validate(df_equal, 'col')
    print("✓ MinValue: value == min_value passes (>= comparison)")
except:
    print("✗ BUG FOUND: MinValue rejects value == min_value (using > instead of >=)")

try:
    min_constraint.validate(df_less, 'col')
    print("✗ BUG: value < min_value should fail")
except:
    print("✓ MinValue: value < min_value correctly fails")

# Check MaxValueColumnConstraint source for operator  
# Line 1056 in constraints.py: invalid = dataframe[column_name] > self.max_value
# This means values GREATER THAN max_value are invalid
# So values <= max_value should be valid

print("\nChecking MaxValueColumnConstraint implementation...")
max_constraint = MaxValueColumnConstraint(10, ignore_missing_vals=False)

df_equal = pd.DataFrame({'col': [10]})
df_greater = pd.DataFrame({'col': [10.00001]})

try:
    max_constraint.validate(df_equal, 'col')
    print("✓ MaxValue: value == max_value passes (<= comparison)")
except:
    print("✗ BUG FOUND: MaxValue rejects value == max_value (using < instead of <=)")

try:
    max_constraint.validate(df_greater, 'col')
    print("✗ BUG: value > max_value should fail")
except:
    print("✓ MaxValue: value > max_value correctly fails")

print("\n" + "=" * 60)
print("Testing complete!")