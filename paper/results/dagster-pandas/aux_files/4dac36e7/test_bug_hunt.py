"""Focused bug hunting tests for dagster_pandas.validation module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-pandas_env/lib/python3.13/site-packages')

import pandas as pd
import numpy as np
from hypothesis import given, strategies as st, assume, settings, example
from dagster import DagsterInvariantViolationError
from dagster_pandas.validation import (
    PandasColumn,
    validate_constraints,
)
from dagster_pandas.constraints import (
    CategoricalColumnConstraint,
    ConstraintViolationException,
    ColumnConstraintViolationException,
    RowCountConstraint,
)
from pandas import DataFrame
import pytest


# Bug Hunt 1: CategoricalColumnConstraint with non-string categories
@given(
    categories=st.lists(st.integers(), min_size=1, max_size=5, unique=True),
    test_values=st.lists(st.integers(), min_size=1, max_size=10)
)
def test_categorical_constraint_non_string_categories(categories, test_values):
    """Test categorical constraint with non-string categories.
    
    The code at line 986 in constraints.py has:
    self.categories = list(check.set_param(categories, "categories", of_type=str))
    
    This suggests it expects string categories, but what happens with non-strings?
    """
    df = pd.DataFrame({'test_col': test_values})
    
    # Try to create constraint with integer categories
    # This should fail because of_type=str parameter check
    with pytest.raises(Exception):  # Should raise a type check error
        constraint = CategoricalColumnConstraint(
            categories=set(categories),  # Non-string categories
            ignore_missing_vals=False
        )


# Bug Hunt 2: Test RowCountConstraint with tolerance greater than expected rows
def test_row_count_constraint_invalid_tolerance():
    """Test RowCountConstraint with error_tolerance > num_allowed_rows.
    
    Line 349-350 in constraints.py checks this condition and should raise ValueError.
    """
    # This should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        constraint = RowCountConstraint(
            num_allowed_rows=5,
            error_tolerance=10  # Greater than num_allowed_rows
        )
    assert "Tolerance can't be greater than the number of rows you expect" in str(exc_info.value)


# Bug Hunt 3: Test categorical_column with mixed types in of_types parameter
@given(
    categories=st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=3, unique=True),
    test_mixed_types=st.booleans()
)
def test_categorical_column_of_types_handling(categories, test_mixed_types):
    """Test categorical_column with of_types parameter.
    
    Line 359 in validation.py converts single string to set:
    of_types = {of_types} if isinstance(of_types, str) else of_types
    """
    if test_mixed_types:
        # Mix strings and objects in dataframe
        test_values = categories[:1] + [123, None]  # Mixed types
    else:
        test_values = categories
    
    df = pd.DataFrame({'test_col': test_values})
    
    # Test with single string of_types
    cat_col = PandasColumn.categorical_column(
        name='test_col',
        categories=categories,
        of_types='object',  # Single string, will be converted to set
        non_nullable=False
    )
    
    # Should validate based on dtype constraint
    try:
        cat_col.validate(df)
    except ColumnConstraintViolationException as e:
        # Check if it's failing on the right constraint
        if "dtype" in str(e).lower():
            pass  # Expected if dtype doesn't match
        else:
            raise


# Bug Hunt 4: Test unique constraint with pandas special values
@given(ignore_missing=st.booleans())
def test_unique_constraint_pandas_nat(ignore_missing):
    """Test unique constraint with pandas NaT (Not a Time) values."""
    # Create DataFrame with NaT values
    df = pd.DataFrame({
        'test_col': [pd.NaT, pd.NaT, pd.Timestamp('2023-01-01')]
    })
    
    constraint = UniqueColumnConstraint(ignore_missing_vals=ignore_missing)
    
    # NaT values should behave like NaN - considered duplicates when not ignoring
    if not ignore_missing:
        with pytest.raises(ColumnConstraintViolationException):
            constraint.validate(df, 'test_col')
    else:
        # Should pass when ignoring missing values
        constraint.validate(df, 'test_col')


# Bug Hunt 5: Test float column with integer dtype
def test_float_column_with_integer_dtype():
    """Test float_column constraint on integer dtype data.
    
    float_column uses is_float_dtype check which should fail on integer columns.
    """
    df = pd.DataFrame({'test_col': [1, 2, 3]})  # Integer dtype
    
    float_col = PandasColumn.float_column(
        name='test_col',
        min_value=0,
        max_value=10
    )
    
    # Should fail because dtype is int, not float
    with pytest.raises(ColumnConstraintViolationException) as exc_info:
        float_col.validate(df)
    assert "is_float_dtype" in str(exc_info.value)


# Bug Hunt 6: Test boolean column with nullable boolean dtype (pandas 1.0+)
def test_boolean_column_with_nullable_boolean():
    """Test boolean_column with pandas nullable boolean dtype."""
    # Create DataFrame with nullable boolean dtype
    df = pd.DataFrame({
        'test_col': pd.array([True, False, None], dtype='boolean')
    })
    
    bool_col = PandasColumn.boolean_column(
        name='test_col',
        non_nullable=False,  # Allow nulls
        ignore_missing_vals=True
    )
    
    # This might fail depending on how is_bool_dtype handles nullable boolean
    try:
        bool_col.validate(df)
    except ColumnConstraintViolationException as e:
        # Check what constraint failed
        if "is_bool_dtype" in str(e):
            # Nullable boolean might not be recognized as bool dtype
            pass


# Bug Hunt 7: Test string column with mixed string types
def test_string_column_with_object_dtype():
    """Test string_column with object dtype containing strings."""
    # Create DataFrame with object dtype (common for strings)
    df = pd.DataFrame({'test_col': ['a', 'b', 'c']})
    
    # Verify it's object dtype
    assert df['test_col'].dtype == 'object'
    
    string_col = PandasColumn.string_column(
        name='test_col',
        non_nullable=False
    )
    
    # Should work with object dtype containing strings
    string_col.validate(df)


# Bug Hunt 8: Test datetime column with mixed timezones
def test_datetime_column_mixed_timezones():
    """Test datetime column when DataFrame has mixed timezone data."""
    # Try to create DataFrame with mixed timezones (this usually fails in pandas)
    try:
        df = pd.DataFrame({
            'test_col': [
                pd.Timestamp('2023-01-01', tz='UTC'),
                pd.Timestamp('2023-01-01', tz='US/Eastern')  # Different timezone
            ]
        })
    except Exception:
        # Pandas doesn't allow mixed timezones in a single column
        # This is expected behavior
        return
    
    # If we somehow get here, test the constraint
    datetime_col = PandasColumn.datetime_column(
        name='test_col',
        tz='UTC'
    )
    
    with pytest.raises(ColumnConstraintViolationException):
        datetime_col.validate(df)


# Bug Hunt 9: Test validate_constraints with None constraints
def test_validate_constraints_with_none():
    """Test validate_constraints function with None values."""
    df = pd.DataFrame({'col': [1, 2, 3]})
    
    # Should handle None gracefully
    validate_constraints(df, pandas_columns=None, dataframe_constraints=None)
    
    # Should also handle empty lists
    validate_constraints(df, pandas_columns=[], dataframe_constraints=[])


# Bug Hunt 10: Test column constraint on non-existent column
@given(column_name=st.text(min_size=1, max_size=10))
def test_constraint_on_nonexistent_column(column_name):
    """Test applying constraints to non-existent columns."""
    df = pd.DataFrame({'other_col': [1, 2, 3]})
    
    # Create column that doesn't exist
    assume(column_name != 'other_col')
    
    pandas_col = PandasColumn.numeric_column(
        name=column_name,
        min_value=0,
        max_value=10,
        is_required=True  # Required column
    )
    
    # Should fail because column doesn't exist
    with pytest.raises(ConstraintViolationException) as exc_info:
        pandas_col.validate(df)
    assert f"Required column {column_name} not in dataframe" in str(exc_info.value)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x", "--hypothesis-show-statistics"])