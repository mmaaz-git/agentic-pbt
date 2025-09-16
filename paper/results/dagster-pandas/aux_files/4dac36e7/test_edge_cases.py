"""Edge case property-based tests for dagster_pandas.validation module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-pandas_env/lib/python3.13/site-packages')

import pandas as pd
import numpy as np
from hypothesis import given, strategies as st, assume, settings, note
from dagster import DagsterInvariantViolationError
from dagster_pandas.validation import (
    PandasColumn,
    validate_constraints,
)
from dagster_pandas.constraints import (
    InRangeColumnConstraint,
    UniqueColumnConstraint,
    CategoricalColumnConstraint,
    ConstraintViolationException,
    ColumnConstraintViolationException,
    NonNullableColumnConstraint,
    StrictColumnsConstraint,
    RowCountConstraint,
)
from pandas import DataFrame, Timestamp
import pytest
from datetime import datetime, timezone
import math


# Edge Case 1: Test with infinity values in numeric columns
@given(
    include_inf=st.booleans(),
    include_neg_inf=st.booleans(),
    min_val=st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False),
    max_val=st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False)
)
def test_numeric_column_with_infinity(include_inf, include_neg_inf, min_val, max_val):
    """Test numeric columns with infinity values."""
    assume(min_val <= max_val)
    
    values = []
    if include_inf:
        values.append(float('inf'))
    if include_neg_inf:
        values.append(float('-inf'))
    if not values:
        values = [0.0]  # Add a regular value
    
    df = pd.DataFrame({'test_col': values})
    
    numeric_col = PandasColumn.numeric_column(
        name='test_col',
        min_value=min_val,
        max_value=max_val,
        non_nullable=False,
        unique=False,
        ignore_missing_vals=False
    )
    
    # Infinity values should fail range validation
    if include_inf or include_neg_inf:
        with pytest.raises(ColumnConstraintViolationException):
            numeric_col.validate(df)


# Edge Case 2: Test with NaN values in unique constraint
@given(
    num_nans=st.integers(min_value=0, max_value=5),
    num_regular=st.integers(min_value=0, max_value=5),
    ignore_missing=st.booleans()
)
def test_unique_constraint_with_multiple_nans(num_nans, num_regular, ignore_missing):
    """Test unique constraint with multiple NaN values."""
    values = []
    
    # Add NaN values
    for _ in range(num_nans):
        values.append(np.nan)
    
    # Add unique regular values
    for i in range(num_regular):
        values.append(float(i))
    
    if not values:
        values = [1.0]  # Ensure non-empty dataframe
    
    df = pd.DataFrame({'test_col': values})
    constraint = UniqueColumnConstraint(ignore_missing_vals=ignore_missing)
    
    # NaN values are not considered equal to each other in pandas
    # So multiple NaNs should not violate uniqueness
    # However, the duplicated() method in pandas does consider NaN as duplicate
    
    if num_nans > 1 and not ignore_missing:
        # Multiple NaNs are considered duplicates when not ignoring missing
        with pytest.raises(ColumnConstraintViolationException):
            constraint.validate(df, 'test_col')
    else:
        # Should pass
        constraint.validate(df, 'test_col')


# Edge Case 3: Test empty DataFrame validation
@given(
    column_names=st.lists(
        st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
        min_size=0,
        max_size=5,
        unique=True
    ),
    required=st.booleans()
)
def test_empty_dataframe_validation(column_names, required):
    """Test validation on empty DataFrames."""
    # Create empty DataFrame with specified columns
    df = pd.DataFrame(columns=column_names)
    
    if column_names:
        # Test with a column that exists but has no data
        col_name = column_names[0]
        pandas_col = PandasColumn(
            name=col_name,
            constraints=[NonNullableColumnConstraint()],
            is_required=required
        )
        
        # Empty DataFrame should pass - no rows to violate constraints
        pandas_col.validate(df)
    else:
        # Test with a column that doesn't exist
        pandas_col = PandasColumn(
            name='nonexistent',
            constraints=[],
            is_required=required
        )
        
        if required:
            with pytest.raises(ConstraintViolationException):
                pandas_col.validate(df)
        else:
            pandas_col.validate(df)


# Edge Case 4: Test categorical constraint with empty categories
@given(
    test_values=st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=5),
    ignore_missing=st.booleans()
)
def test_categorical_constraint_empty_categories(test_values, ignore_missing):
    """Test categorical constraint with empty category set."""
    df = pd.DataFrame({'test_col': test_values})
    
    # Empty categories set - nothing should be valid
    constraint = CategoricalColumnConstraint(
        categories=set(),  # Empty set
        ignore_missing_vals=ignore_missing
    )
    
    # All values should fail validation (empty categories)
    with pytest.raises(ColumnConstraintViolationException):
        constraint.validate(df, 'test_col')


# Edge Case 5: Test datetime at boundaries
@given(use_tz=st.booleans())
def test_datetime_boundary_values(use_tz):
    """Test datetime columns with boundary timestamp values."""
    if use_tz:
        # Test with timezone-aware timestamps near boundaries
        # These are the adjusted boundaries from the code
        min_dt = Timestamp("1677-09-22 00:12:43.145225Z")
        max_dt = Timestamp("2262-04-10 23:47:16.854775807Z")
        test_dt = Timestamp("2000-01-01 00:00:00Z")
        
        df = pd.DataFrame({'test_col': [test_dt]})
        
        datetime_col = PandasColumn.datetime_column(
            name='test_col',
            min_datetime=Timestamp.min,  # Will be adjusted internally
            max_datetime=Timestamp.max,  # Will be adjusted internally
            tz='UTC'
        )
        
        # Should handle boundary adjustments correctly
        datetime_col.validate(df)


# Edge Case 6: Test StrictColumnsConstraint ordering
@given(
    columns=st.lists(
        st.text(min_size=1, max_size=5, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
        min_size=2,
        max_size=5,
        unique=True
    ),
    enforce_ordering=st.booleans()
)
def test_strict_columns_ordering(columns, enforce_ordering):
    """Test StrictColumnsConstraint with column ordering."""
    # Create DataFrame with columns in specific order
    df = pd.DataFrame({col: [1, 2, 3] for col in columns})
    
    # Create constraint with potentially different order
    shuffled_columns = columns.copy()
    if len(shuffled_columns) > 1:
        # Swap first and last to ensure different order
        shuffled_columns[0], shuffled_columns[-1] = shuffled_columns[-1], shuffled_columns[0]
    
    constraint = StrictColumnsConstraint(
        strict_column_list=shuffled_columns,
        enforce_ordering=enforce_ordering
    )
    
    if enforce_ordering and columns != shuffled_columns:
        # Should fail due to ordering mismatch
        with pytest.raises(ConstraintViolationException):
            constraint.validate(df)
    else:
        # Should pass (either ordering not enforced or order matches)
        constraint.validate(df)


# Edge Case 7: Test RowCountConstraint with error tolerance
@given(
    expected_rows=st.integers(min_value=0, max_value=1000),
    actual_rows=st.integers(min_value=0, max_value=1000),
    tolerance=st.integers(min_value=0, max_value=100)
)
def test_row_count_constraint_tolerance(expected_rows, actual_rows, tolerance):
    """Test RowCountConstraint with error tolerance."""
    assume(tolerance <= expected_rows)  # Constraint requirement
    
    # Create DataFrame with actual_rows rows
    df = pd.DataFrame({'col': range(actual_rows)})
    
    constraint = RowCountConstraint(
        num_allowed_rows=expected_rows,
        error_tolerance=tolerance
    )
    
    # Check if actual rows are within tolerance
    within_tolerance = (expected_rows - tolerance <= actual_rows <= expected_rows + tolerance)
    
    if within_tolerance:
        constraint.validate(df)
    else:
        with pytest.raises(ConstraintViolationException):
            constraint.validate(df)


# Edge Case 8: Test integer column with float values that are integers
@given(
    values=st.lists(
        st.floats(min_value=-1000, max_value=1000, allow_nan=False),
        min_size=1,
        max_size=10
    )
)
def test_integer_column_with_float_integers(values):
    """Test integer column validation with float values that are whole numbers."""
    # Convert some values to be exact integers (as floats)
    for i in range(0, len(values), 2):
        values[i] = float(int(values[i]))
    
    df = pd.DataFrame({'test_col': values})
    
    integer_col = PandasColumn.integer_column(
        name='test_col',
        min_value=-float('inf'),
        max_value=float('inf')
    )
    
    # This should fail because the dtype is float, not integer
    # even if the values are whole numbers
    with pytest.raises(ColumnConstraintViolationException):
        integer_col.validate(df)


# Edge Case 9: Test validate_constraints with multiple failing constraints
@given(
    num_values=st.integers(min_value=5, max_value=20),
    add_duplicates=st.booleans(),
    add_nulls=st.booleans()
)
def test_multiple_constraint_failures(num_values, add_duplicates, add_nulls):
    """Test behavior when multiple constraints fail on the same column."""
    values = list(range(num_values))
    
    if add_duplicates:
        values.append(values[0])  # Add duplicate
    
    if add_nulls:
        values[1] = np.nan  # Add null
    
    df = pd.DataFrame({'test_col': values})
    
    # Create column with multiple constraints that might fail
    constraints = []
    if add_nulls:
        constraints.append(NonNullableColumnConstraint())
    if add_duplicates:
        constraints.append(UniqueColumnConstraint(ignore_missing_vals=False))
    
    if constraints:
        pandas_col = PandasColumn(
            name='test_col',
            constraints=constraints,
            is_required=True
        )
        
        # Should fail on the first constraint violation
        with pytest.raises(ConstraintViolationException):
            pandas_col.validate(df)


# Edge Case 10: Test special pandas index edge cases  
@given(
    use_multi_index=st.booleans(),
    num_rows=st.integers(min_value=1, max_value=10)
)
def test_dataframe_with_special_index(use_multi_index, num_rows):
    """Test validation with special DataFrame index types."""
    if use_multi_index:
        # Create MultiIndex DataFrame
        index = pd.MultiIndex.from_product(
            [['A', 'B'], range(num_rows // 2 + 1)],
            names=['letter', 'number']
        )[:num_rows]
        df = pd.DataFrame({'col': range(num_rows)}, index=index)
    else:
        # Create DataFrame with non-integer index
        df = pd.DataFrame(
            {'col': range(num_rows)},
            index=[f'row_{i}' for i in range(num_rows)]
        )
    
    # Constraints should work regardless of index type
    constraint = NonNullableColumnConstraint()
    constraint.validate(df, 'col')


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])