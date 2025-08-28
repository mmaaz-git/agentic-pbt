#!/usr/bin/env /root/hypothesis-llm/envs/dagster-pandas_env/bin/python

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-pandas_env/lib/python3.13/site-packages')

import pandas as pd
import numpy as np
from hypothesis import given, strategies as st, assume, settings
from hypothesis.extra import pandas as pdst
import math
from datetime import datetime

# Import the dagster_pandas modules
from dagster_pandas.constraints import (
    StrictColumnsConstraint,
    RowCountConstraint,
    InRangeColumnConstraint,
    MinValueColumnConstraint,
    MaxValueColumnConstraint,
    DataFrameConstraintViolationException,
    ColumnConstraintViolationException,
)
from dagster_pandas.data_frame import create_table_schema_metadata_from_dataframe


# Property 1: StrictColumnsConstraint with enforce_ordering
# The documentation claims that when enforce_ordering=True, columns must match exactly in order
@given(
    column_names=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5, unique=True),
    permute=st.booleans()
)
def test_strict_columns_ordering(column_names, permute):
    """Test that StrictColumnsConstraint correctly enforces column ordering when required."""
    
    # Create a DataFrame with the given columns
    df = pd.DataFrame(columns=column_names)
    
    # Create the constraint with enforce_ordering=True
    constraint = StrictColumnsConstraint(column_names, enforce_ordering=True)
    
    # This should pass validation
    constraint.validate(df)
    
    if permute and len(column_names) > 1:
        # Permute the columns
        import random
        permuted_columns = column_names.copy()
        random.shuffle(permuted_columns)
        assume(permuted_columns != column_names)  # Only test when actually permuted
        
        df_permuted = pd.DataFrame(columns=permuted_columns)
        
        # This should fail validation since ordering is enforced
        try:
            constraint.validate(df_permuted)
            assert False, "Should have raised DataFrameConstraintViolationException"
        except DataFrameConstraintViolationException:
            pass  # Expected


# Property 2: StrictColumnsConstraint without enforce_ordering
# When enforce_ordering=False, only column presence matters, not order
@given(
    column_names=st.lists(st.text(min_size=1, max_size=10), min_size=2, max_size=5, unique=True)
)
def test_strict_columns_no_ordering(column_names):
    """Test that StrictColumnsConstraint ignores ordering when enforce_ordering=False."""
    
    # Create constraint without ordering enforcement
    constraint = StrictColumnsConstraint(column_names, enforce_ordering=False)
    
    # Test with different orderings
    import random
    permuted = column_names.copy()
    random.shuffle(permuted)
    
    df = pd.DataFrame(columns=permuted)
    
    # Should pass since we have the same columns (just different order)
    constraint.validate(df)


# Property 3: RowCountConstraint error_tolerance invariant
# The code checks that error_tolerance cannot be greater than num_allowed_rows
@given(
    num_rows=st.integers(min_value=0, max_value=1000),
    tolerance=st.integers(min_value=0, max_value=2000)
)
def test_row_count_tolerance_invariant(num_rows, tolerance):
    """Test that RowCountConstraint enforces tolerance <= num_allowed_rows."""
    
    if tolerance > num_rows:
        # Should raise ValueError
        try:
            constraint = RowCountConstraint(num_rows, error_tolerance=tolerance)
            assert False, "Should have raised ValueError for tolerance > num_rows"
        except ValueError as e:
            assert "Tolerance can't be greater than the number of rows you expect" in str(e)
    else:
        # Should create successfully
        constraint = RowCountConstraint(num_rows, error_tolerance=tolerance)
        assert constraint.num_allowed_rows == num_rows
        assert constraint.error_tolerance == abs(tolerance)


# Property 4: InRangeColumnConstraint bounds checking
# Values should be between min_value and max_value inclusive
@given(
    data=st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6), min_size=1, max_size=100),
    min_val=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
    max_val=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6)
)
def test_in_range_constraint_bounds(data, min_val, max_val):
    """Test that InRangeColumnConstraint correctly validates bounds."""
    
    assume(min_val <= max_val)  # Ensure valid range
    
    df = pd.DataFrame({'test_col': data})
    constraint = InRangeColumnConstraint(min_val, max_val, ignore_missing_vals=False)
    
    # Check if all values are in range
    all_in_range = all(min_val <= val <= max_val for val in data)
    
    if all_in_range:
        # Should pass validation
        constraint.validate(df, 'test_col')
    else:
        # Should fail validation
        try:
            constraint.validate(df, 'test_col')
            assert False, "Should have raised ColumnConstraintViolationException"
        except ColumnConstraintViolationException:
            pass  # Expected


# Property 5: MinValue and MaxValue constraint boundary conditions
# Test that <= and >= comparisons work correctly at boundaries
@given(
    boundary=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
    epsilon=st.floats(min_value=1e-10, max_value=1e-6)
)
def test_min_max_value_boundaries(boundary, epsilon):
    """Test MinValue and MaxValue constraints at exact boundaries."""
    
    # Test MinValueColumnConstraint
    min_constraint = MinValueColumnConstraint(boundary, ignore_missing_vals=False)
    
    # Value exactly at boundary should pass
    df_exact = pd.DataFrame({'col': [boundary]})
    min_constraint.validate(df_exact, 'col')  # Should not raise
    
    # Value slightly below should fail
    df_below = pd.DataFrame({'col': [boundary - epsilon]})
    try:
        min_constraint.validate(df_below, 'col')
        assert False, "Should have raised for value below minimum"
    except ColumnConstraintViolationException:
        pass  # Expected
    
    # Test MaxValueColumnConstraint
    max_constraint = MaxValueColumnConstraint(boundary, ignore_missing_vals=False)
    
    # Value exactly at boundary should pass
    max_constraint.validate(df_exact, 'col')  # Should not raise
    
    # Value slightly above should fail
    df_above = pd.DataFrame({'col': [boundary + epsilon]})
    try:
        max_constraint.validate(df_above, 'col')
        assert False, "Should have raised for value above maximum"
    except ColumnConstraintViolationException:
        pass  # Expected


# Property 6: create_table_schema_metadata preserves DataFrame structure
# The function should accurately capture column names and types
@given(
    df=pdst.data_frames(
        columns=[
            pdst.column(name='int_col', dtype=int),
            pdst.column(name='float_col', dtype=float),
            pdst.column(name='str_col', dtype=str),
        ],
        rows=st.integers(min_value=0, max_value=10)
    )
)
def test_table_schema_metadata_preserves_structure(df):
    """Test that create_table_schema_metadata_from_dataframe preserves column information."""
    
    # Create metadata
    metadata = create_table_schema_metadata_from_dataframe(df)
    
    # Extract the table schema
    table_schema = metadata.value
    
    # Check that all columns are present
    schema_columns = {col.name for col in table_schema.columns}
    df_columns = set(df.columns.astype(str))
    
    assert schema_columns == df_columns, f"Column names mismatch: {schema_columns} != {df_columns}"
    
    # Check column count matches
    assert len(table_schema.columns) == len(df.columns)
    
    # Verify column types are captured (as strings)
    for col in table_schema.columns:
        assert col.type is not None
        assert isinstance(col.type, str)


# Property 7: RowCountConstraint validation logic
# Test the actual validation with tolerance
@given(
    expected_rows=st.integers(min_value=1, max_value=100),
    tolerance=st.integers(min_value=0, max_value=50),
    actual_rows=st.integers(min_value=0, max_value=150)
)
def test_row_count_validation_logic(expected_rows, tolerance, actual_rows):
    """Test that RowCountConstraint correctly validates row counts with tolerance."""
    
    assume(tolerance <= expected_rows)  # Ensure valid constraint
    
    constraint = RowCountConstraint(expected_rows, error_tolerance=tolerance)
    
    # Create DataFrame with actual_rows
    df = pd.DataFrame({'col': range(actual_rows)})
    
    # Check if within tolerance
    within_tolerance = (expected_rows - tolerance) <= actual_rows <= (expected_rows + tolerance)
    
    if within_tolerance:
        # Should pass
        constraint.validate(df)
    else:
        # Should fail
        try:
            constraint.validate(df)
            assert False, f"Should have raised for {actual_rows} rows (expected {expected_rows} ± {tolerance})"
        except DataFrameConstraintViolationException as e:
            # Verify error message contains the right information
            assert str(expected_rows) in str(e)
            assert str(tolerance) in str(e)
            assert str(actual_rows) in str(e)


if __name__ == "__main__":
    # Run with pytest
    import pytest
    pytest.main([__file__, "-v"])