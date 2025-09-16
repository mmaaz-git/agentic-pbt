"""Property-based tests for dagster_pandas.validation module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-pandas_env/lib/python3.13/site-packages')

import pandas as pd
import numpy as np
from hypothesis import given, strategies as st, assume, settings
from hypothesis.extra import pandas as hp_pandas
from dagster import DagsterInvariantViolationError
from dagster_pandas.validation import (
    PandasColumn,
    _construct_keyword_constraints,
    validate_constraints,
)
from dagster_pandas.constraints import (
    InRangeColumnConstraint,
    UniqueColumnConstraint,
    CategoricalColumnConstraint,
    ConstraintViolationException,
    ColumnConstraintViolationException,
    NonNullableColumnConstraint,
)
from pandas import DataFrame, Timestamp
import pytest
from datetime import datetime, timezone


# Property 1: Invariant - non_nullable and ignore_missing_vals cannot both be True
@given(
    non_nullable=st.booleans(),
    unique=st.booleans(),
    ignore_missing_vals=st.booleans()
)
def test_construct_keyword_constraints_invariant(non_nullable, unique, ignore_missing_vals):
    """Test that non_nullable and ignore_missing_vals cannot both be True."""
    if non_nullable and ignore_missing_vals:
        # This should raise an exception
        with pytest.raises(DagsterInvariantViolationError) as exc_info:
            _construct_keyword_constraints(non_nullable, unique, ignore_missing_vals)
        assert "cannot have a non-null constraint while also ignore missing values" in str(exc_info.value)
    else:
        # This should work fine
        constraints = _construct_keyword_constraints(non_nullable, unique, ignore_missing_vals)
        assert isinstance(constraints, list)
        
        # Verify constraints are correctly created
        if non_nullable:
            assert any(isinstance(c, NonNullableColumnConstraint) for c in constraints)
        if unique:
            assert any(isinstance(c, UniqueColumnConstraint) for c in constraints)


# Property 2: InRangeColumnConstraint boundary inclusivity
@given(
    min_val=st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False),
    max_val=st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False),
)
def test_in_range_constraint_boundary_inclusive(min_val, max_val):
    """Test that InRangeColumnConstraint includes boundary values."""
    assume(min_val <= max_val)  # Ensure valid range
    
    # Create a dataframe with boundary values
    df = pd.DataFrame({
        'test_col': [min_val, max_val, (min_val + max_val) / 2]
    })
    
    constraint = InRangeColumnConstraint(
        min_value=min_val,
        max_value=max_val,
        ignore_missing_vals=False
    )
    
    # Boundary values should pass (inclusive range)
    try:
        constraint.validate(df, 'test_col')
        # If no exception, the test passes
    except ColumnConstraintViolationException:
        pytest.fail(f"Boundary values {min_val} and {max_val} should be included in range [{min_val}, {max_val}]")


# Property 3: InRangeColumnConstraint out of bounds detection
@given(
    min_val=st.floats(min_value=-1e5, max_value=1e5, allow_nan=False, allow_infinity=False),
    max_val=st.floats(min_value=-1e5, max_value=1e5, allow_nan=False, allow_infinity=False),
    out_of_bounds_val=st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False)
)
def test_in_range_constraint_out_of_bounds(min_val, max_val, out_of_bounds_val):
    """Test that values outside the range are correctly rejected."""
    assume(min_val < max_val)  # Ensure valid range
    assume(out_of_bounds_val < min_val or out_of_bounds_val > max_val)  # Ensure value is out of bounds
    
    df = pd.DataFrame({
        'test_col': [out_of_bounds_val]
    })
    
    constraint = InRangeColumnConstraint(
        min_value=min_val,
        max_value=max_val,
        ignore_missing_vals=False
    )
    
    # Out of bounds values should fail
    with pytest.raises(ColumnConstraintViolationException) as exc_info:
        constraint.validate(df, 'test_col')
    
    assert f"between {min_val} and {max_val}" in str(exc_info.value)


# Property 4: UniqueColumnConstraint duplicate detection
@given(
    values=st.lists(st.integers(min_value=0, max_value=100), min_size=2, max_size=20),
    ignore_missing=st.booleans()
)
def test_unique_constraint_duplicate_detection(values, ignore_missing):
    """Test that UniqueColumnConstraint correctly detects duplicates."""
    # Ensure we have at least one duplicate
    if len(set(values)) == len(values):
        # Force a duplicate
        values.append(values[0])
    
    # Optionally add some NaN values
    if ignore_missing and len(values) > 3:
        values[1] = np.nan
        values[2] = np.nan  # Duplicate NaN
    
    df = pd.DataFrame({'test_col': values})
    constraint = UniqueColumnConstraint(ignore_missing_vals=ignore_missing)
    
    # Count non-NaN duplicates
    series = df['test_col']
    if ignore_missing:
        # When ignoring missing values, NaN duplicates should be ignored
        non_nan_series = series.dropna()
        has_non_nan_duplicates = non_nan_series.duplicated().any()
    else:
        # When not ignoring missing values, all duplicates count
        has_non_nan_duplicates = series.duplicated().any()
    
    if has_non_nan_duplicates:
        with pytest.raises(ColumnConstraintViolationException) as exc_info:
            constraint.validate(df, 'test_col')
        assert "must be unique" in str(exc_info.value)
    else:
        # Should pass without exception
        constraint.validate(df, 'test_col')


# Property 5: CategoricalColumnConstraint validation
@given(
    categories=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5, unique=True),
    test_values=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=10),
    ignore_missing=st.booleans()
)
def test_categorical_constraint_validation(categories, test_values, ignore_missing):
    """Test that CategoricalColumnConstraint correctly validates categories."""
    # Convert to set for proper categorical constraint
    categories_set = set(categories)
    
    # Add some NaN values if testing ignore_missing
    if ignore_missing and len(test_values) > 2:
        test_values[0] = np.nan
    
    df = pd.DataFrame({'test_col': test_values})
    constraint = CategoricalColumnConstraint(
        categories=categories_set,
        ignore_missing_vals=ignore_missing
    )
    
    # Check if all non-null values are in categories
    series = df['test_col']
    if ignore_missing:
        invalid_mask = ~series.isin(categories_set) & series.notna()
    else:
        invalid_mask = ~series.isin(categories_set)
    
    has_invalid = invalid_mask.any()
    
    if has_invalid:
        with pytest.raises(ColumnConstraintViolationException) as exc_info:
            constraint.validate(df, 'test_col')
        assert "Expected Categories" in str(exc_info.value)
    else:
        # Should pass without exception
        constraint.validate(df, 'test_col')


# Property 6: PandasColumn required column validation
@given(
    column_name=st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    is_required=st.booleans(),
    df_columns=st.lists(
        st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
        min_size=0,
        max_size=5,
        unique=True
    )
)
def test_pandas_column_required_validation(column_name, is_required, df_columns):
    """Test that PandasColumn correctly validates required columns."""
    # Create a dataframe with the specified columns
    data = {col: [1, 2, 3] for col in df_columns}
    df = pd.DataFrame(data) if data else pd.DataFrame({'dummy': [1]})
    
    # Create a PandasColumn
    pandas_col = PandasColumn(
        name=column_name,
        constraints=[],
        is_required=is_required
    )
    
    # Check if column exists in dataframe
    column_exists = column_name in df.columns
    
    if is_required and not column_exists:
        # Should raise exception for missing required column
        with pytest.raises(ConstraintViolationException) as exc_info:
            pandas_col.validate(df)
        assert f"Required column {column_name} not in dataframe" in str(exc_info.value)
    else:
        # Should pass (either column exists or it's not required)
        pandas_col.validate(df)


# Property 7: numeric_column min/max validation
@given(
    min_value=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False),
    max_value=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False),
    test_values=st.lists(
        st.floats(min_value=-1e7, max_value=1e7, allow_nan=False),
        min_size=1,
        max_size=10
    )
)
def test_numeric_column_range_validation(min_value, max_value, test_values):
    """Test that numeric_column correctly validates min/max constraints."""
    assume(min_value <= max_value)
    
    df = pd.DataFrame({'test_col': test_values})
    
    # Create numeric column with range constraints
    numeric_col = PandasColumn.numeric_column(
        name='test_col',
        min_value=min_value,
        max_value=max_value,
        non_nullable=False,
        unique=False,
        ignore_missing_vals=False
    )
    
    # Check if all values are in range
    all_in_range = all(min_value <= v <= max_value for v in test_values)
    
    if all_in_range:
        # Should pass
        numeric_col.validate(df)
    else:
        # Should fail
        with pytest.raises(ColumnConstraintViolationException):
            numeric_col.validate(df)


# Property 8: Test datetime column timezone handling  
@given(
    use_tz=st.booleans(),
    tz_str=st.sampled_from(['UTC', 'US/Eastern', 'Europe/Dublin'])
)
@settings(max_examples=50)
def test_datetime_column_timezone_handling(use_tz, tz_str):
    """Test that datetime_column handles timezones correctly."""
    # Create test datetime values
    base_dt = pd.Timestamp('2023-01-15 12:00:00')
    
    if use_tz:
        # Create timezone-aware datetimes
        dt_values = [
            base_dt.tz_localize(tz_str),
            pd.Timestamp('2023-06-15 12:00:00').tz_localize(tz_str),
            pd.Timestamp('2023-12-15 12:00:00').tz_localize(tz_str)
        ]
        expected_dtype = f'datetime64[ns, {tz_str}]'
    else:
        # Create timezone-naive datetimes
        dt_values = [
            base_dt,
            pd.Timestamp('2023-06-15 12:00:00'),
            pd.Timestamp('2023-12-15 12:00:00')
        ]
        expected_dtype = 'datetime64[ns]'
    
    df = pd.DataFrame({'test_col': dt_values})
    
    # Create datetime column
    datetime_col = PandasColumn.datetime_column(
        name='test_col',
        min_datetime=pd.Timestamp('2020-01-01').tz_localize(tz_str) if use_tz else pd.Timestamp('2020-01-01'),
        max_datetime=pd.Timestamp('2025-01-01').tz_localize(tz_str) if use_tz else pd.Timestamp('2025-01-01'),
        tz=tz_str if use_tz else None
    )
    
    # Should validate successfully
    datetime_col.validate(df)
    
    # Verify the dtype constraint is correct
    assert str(df['test_col'].dtype) == expected_dtype


if __name__ == "__main__":
    # Run the tests
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))