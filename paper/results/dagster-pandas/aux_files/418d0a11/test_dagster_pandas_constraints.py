import sys
import pandas as pd
import numpy as np
from hypothesis import given, strategies as st, assume, settings
from hypothesis.extra.pandas import data_frames, column, range_indexes, columns
import pytest
from datetime import datetime, timedelta
import math

# Add the venv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-pandas_env/lib/python3.13/site-packages')

from dagster_pandas.constraints import (
    RowCountConstraint,
    StrictColumnsConstraint,
    column_range_validation_factory,
    all_unique_validator,
    InRangeColumnConstraint,
    ConstraintWithMetadataException,
    categorical_column_validator_factory,
    StrictColumnsWithMetadata,
    MinValueColumnConstraint,
    MaxValueColumnConstraint,
    DataFrameConstraintViolationException,
    ColumnConstraintViolationException
)


# Test 1: RowCountConstraint invariants
@given(
    num_allowed_rows=st.integers(min_value=0, max_value=10000),
    error_tolerance=st.integers(min_value=0, max_value=10000),
    actual_rows=st.integers(min_value=0, max_value=20000)
)
def test_row_count_constraint_invariants(num_allowed_rows, error_tolerance, actual_rows):
    """Test that RowCountConstraint correctly validates row counts within tolerance."""
    
    # Property 1: error_tolerance cannot be greater than num_allowed_rows
    if error_tolerance > num_allowed_rows:
        with pytest.raises(ValueError, match="Tolerance can't be greater than the number of rows you expect"):
            RowCountConstraint(num_allowed_rows, error_tolerance)
        return
    
    constraint = RowCountConstraint(num_allowed_rows, error_tolerance)
    df = pd.DataFrame({'a': range(actual_rows)})
    
    # Property 2: Values within range should pass, outside should fail
    within_range = (num_allowed_rows - error_tolerance <= actual_rows <= num_allowed_rows + error_tolerance)
    
    if within_range:
        constraint.validate(df)  # Should not raise
    else:
        with pytest.raises(DataFrameConstraintViolationException):
            constraint.validate(df)


# Test 2: StrictColumnsConstraint ordering property
@given(
    columns_list=st.lists(st.text(min_size=1, max_size=10, alphabet=st.characters(categories=['L', 'N'])), 
                          min_size=1, max_size=10, unique=True),
    enforce_ordering=st.booleans()
)
def test_strict_columns_constraint_ordering(columns_list, enforce_ordering):
    """Test that StrictColumnsConstraint correctly validates column ordering."""
    
    constraint = StrictColumnsConstraint(columns_list, enforce_ordering=enforce_ordering)
    
    # Test with exact match
    df_exact = pd.DataFrame(columns=columns_list)
    constraint.validate(df_exact)  # Should not raise
    
    if len(columns_list) > 1:
        # Test with reordered columns
        import random
        shuffled = columns_list.copy()
        random.shuffle(shuffled)
        if shuffled != columns_list:  # Only test if actually shuffled
            df_reordered = pd.DataFrame(columns=shuffled)
            
            if enforce_ordering:
                # Should fail when ordering is enforced and columns are reordered
                with pytest.raises(DataFrameConstraintViolationException):
                    constraint.validate(df_reordered)
            else:
                # Should pass when ordering is not enforced
                constraint.validate(df_reordered)


# Test 3: column_range_validation_factory bounds checking
@given(
    min_val=st.one_of(st.none(), st.integers(min_value=-1000, max_value=1000)),
    max_val=st.one_of(st.none(), st.integers(min_value=-1000, max_value=1000)),
    test_val=st.integers(min_value=-2000, max_value=2000)
)
def test_column_range_validation_factory(min_val, max_val, test_val):
    """Test that column_range_validation_factory correctly validates ranges."""
    
    # Skip invalid ranges
    if min_val is not None and max_val is not None and min_val > max_val:
        assume(False)
    
    validator = column_range_validation_factory(minim=min_val, maxim=max_val)
    
    # Determine effective bounds
    effective_min = min_val if min_val is not None else -(sys.maxsize - 1)
    effective_max = max_val if max_val is not None else sys.maxsize
    
    result, metadata = validator(test_val)
    
    # Property: Values within range (inclusive) should pass
    if effective_min <= test_val <= effective_max:
        assert result == True, f"Value {test_val} should be within range [{effective_min}, {effective_max}]"
    else:
        assert result == False, f"Value {test_val} should be outside range [{effective_min}, {effective_max}]"


# Test 4: all_unique_validator correctness
@given(
    values=st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=100)
)
def test_all_unique_validator(values):
    """Test that all_unique_validator correctly identifies duplicates."""
    
    series = pd.Series(values)
    result, metadata = all_unique_validator(series)
    
    # Property: Should return False if duplicates exist, True otherwise
    has_duplicates = len(values) != len(set(values))
    
    if has_duplicates:
        assert result == False, "Should detect duplicates"
        # Check that metadata contains the duplicated values
        assert "actual" in metadata
        duplicated_values = series[series.duplicated()].tolist()
        assert metadata["actual"].tolist() == duplicated_values
    else:
        assert result == True, "Should pass when all values are unique"
        assert metadata == {} or metadata.get("actual", pd.Series()).empty


# Test 5: InRangeColumnConstraint inclusive bounds
@given(
    min_val=st.floats(min_value=-100.0, max_value=0.0, allow_nan=False, allow_infinity=False),
    max_val=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    test_values=st.lists(st.floats(min_value=-200.0, max_value=200.0, allow_nan=False, allow_infinity=False), 
                        min_size=1, max_size=20)
)
def test_in_range_column_constraint_inclusive(min_val, max_val, test_values):
    """Test that InRangeColumnConstraint correctly validates inclusive bounds."""
    
    assume(min_val <= max_val)
    
    constraint = InRangeColumnConstraint(min_val, max_val, ignore_missing_vals=False)
    df = pd.DataFrame({'test_col': test_values})
    
    # Check if all values are within range (inclusive)
    all_in_range = all(min_val <= v <= max_val for v in test_values)
    
    if all_in_range:
        constraint.validate(df, 'test_col')  # Should not raise
    else:
        with pytest.raises(ColumnConstraintViolationException):
            constraint.validate(df, 'test_col')


# Test 6: ConstraintWithMetadataException.normalize_metadata_json_value
@given(
    value=st.one_of(
        st.sets(st.integers()),
        st.lists(st.integers()),
        st.dictionaries(st.text(min_size=1), st.integers()),
        st.text(),
        st.integers()
    )
)
def test_normalize_metadata_json_value(value):
    """Test that normalize_metadata_json_value correctly converts sets to lists."""
    
    exc = ConstraintWithMetadataException(
        constraint_name="test",
        constraint_description="test description"
    )
    
    normalized = exc.normalize_metadata_json_value(value)
    
    # Property: Sets should be converted to lists, others unchanged
    if isinstance(value, set):
        assert isinstance(normalized, list)
        assert set(normalized) == value
    else:
        assert normalized == value


# Test 7: categorical_column_validator_factory property
@given(
    categories=st.sets(st.integers(min_value=-100, max_value=100), min_size=1, max_size=20),
    test_val=st.integers(min_value=-200, max_value=200)
)
def test_categorical_validator(categories, test_val):
    """Test that categorical_column_validator_factory correctly validates categories."""
    
    validator = categorical_column_validator_factory(categories)
    result, metadata = validator(test_val)
    
    # Property: Values in categories should pass, others should fail
    if test_val in categories:
        assert result == True, f"Value {test_val} should be in categories {categories}"
    else:
        assert result == False, f"Value {test_val} should not be in categories {categories}"


# Test 8: MinValueColumnConstraint and MaxValueColumnConstraint bounds
@given(
    min_bound=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    max_bound=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    test_values=st.lists(st.floats(min_value=-200.0, max_value=200.0, allow_nan=False, allow_infinity=False),
                        min_size=1, max_size=20)
)
def test_min_max_value_constraints(min_bound, max_bound, test_values):
    """Test MinValueColumnConstraint and MaxValueColumnConstraint bounds checking."""
    
    df = pd.DataFrame({'test_col': test_values})
    
    # Test MinValueColumnConstraint
    min_constraint = MinValueColumnConstraint(min_bound, ignore_missing_vals=False)
    all_above_min = all(v >= min_bound for v in test_values)
    
    if all_above_min:
        min_constraint.validate(df, 'test_col')
    else:
        with pytest.raises(ColumnConstraintViolationException):
            min_constraint.validate(df, 'test_col')
    
    # Test MaxValueColumnConstraint  
    max_constraint = MaxValueColumnConstraint(max_bound, ignore_missing_vals=False)
    all_below_max = all(v <= max_bound for v in test_values)
    
    if all_below_max:
        max_constraint.validate(df, 'test_col')
    else:
        with pytest.raises(ColumnConstraintViolationException):
            max_constraint.validate(df, 'test_col')


# Test 9: StrictColumnsWithMetadata ordering property
@given(
    column_list=st.lists(st.text(min_size=1, max_size=10, alphabet=st.characters(categories=['L'])), 
                         min_size=1, max_size=10, unique=True),
    enforce_ordering=st.booleans()
)
def test_strict_columns_with_metadata(column_list, enforce_ordering):
    """Test StrictColumnsWithMetadata correctly validates columns with metadata."""
    
    constraint = StrictColumnsWithMetadata(column_list, enforce_ordering=enforce_ordering)
    
    # Test exact match
    df_exact = pd.DataFrame(columns=column_list)
    result, metadata = constraint.validation_fn(df_exact)
    assert result == True
    
    if len(column_list) > 1:
        # Test with shuffled columns
        import random
        shuffled = column_list.copy()
        random.shuffle(shuffled)
        
        if shuffled != column_list:
            df_shuffled = pd.DataFrame(columns=shuffled)
            result, metadata = constraint.validation_fn(df_shuffled)
            
            if enforce_ordering:
                assert result == False
                assert metadata.get("expectation") == column_list
                assert metadata.get("actual") == shuffled
            else:
                assert result == True


# Test 10: column_range_validation_factory with datetime
@given(
    use_min=st.booleans(),
    use_max=st.booleans(),
    days_offset=st.integers(min_value=-365, max_value=365)
)
def test_column_range_validation_datetime(use_min, use_max, days_offset):
    """Test column_range_validation_factory with datetime values."""
    
    base_date = datetime(2023, 1, 1)
    min_date = base_date if use_min else None
    max_date = base_date + timedelta(days=30) if use_max else None
    test_date = base_date + timedelta(days=days_offset)
    
    validator = column_range_validation_factory(minim=min_date, maxim=max_date)
    result, metadata = validator(test_date)
    
    # Determine effective bounds
    effective_min = min_date if min_date else datetime.min
    effective_max = max_date if max_date else datetime.max
    
    if effective_min <= test_date <= effective_max:
        assert result == True
    else:
        assert result == False


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    pytest.main([__file__, "-v", "--tb=short"])