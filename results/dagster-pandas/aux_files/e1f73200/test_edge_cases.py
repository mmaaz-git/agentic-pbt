import sys
import pandas as pd
import numpy as np
from hypothesis import given, strategies as st, assume, settings
import pytest
from datetime import datetime, timedelta

# Add the site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-pandas_env/lib/python3.13/site-packages/')

from dagster_pandas.constraints import (
    column_range_validation_factory,
    categorical_column_validator_factory, 
    dtype_in_set_validation_factory,
    MultiColumnConstraintWithMetadata,
    ColumnWithMetadataException,
)


# Test edge case: Empty categories set
def test_empty_categories_edge_case():
    """Test categorical validator with empty categories - should always fail."""
    validator = categorical_column_validator_factory([])  # Empty categories
    
    # Any value should fail since no categories are allowed
    result, _ = validator(1)
    assert result == False, "Empty categories should reject all values"
    
    result, _ = validator("test")
    assert result == False, "Empty categories should reject all values"


# Test edge case: Datetime range validation
@given(
    days_offset=st.integers(min_value=-365, max_value=365)
)
def test_datetime_range_validation(days_offset):
    """Test that datetime range validation works correctly."""
    base_date = datetime(2024, 1, 1)
    min_date = base_date
    max_date = base_date + timedelta(days=30)
    test_date = base_date + timedelta(days=days_offset)
    
    validator = column_range_validation_factory(min_date, max_date)
    result, _ = validator(test_date)
    
    expected = (0 <= days_offset <= 30)
    assert result == expected, f"Datetime validation failed for offset {days_offset}"


# Test edge case: Mixed type validation with nulls
@given(
    value=st.one_of(
        st.integers(),
        st.floats(allow_nan=True, allow_infinity=True),
        st.text(),
        st.none()
    ),
    ignore_missing=st.booleans()
)
def test_mixed_type_with_special_values(value, ignore_missing):
    """Test dtype validation with special float values and nulls."""
    validator = dtype_in_set_validation_factory((int, float), ignore_missing_vals=ignore_missing)
    result, _ = validator(value)
    
    if pd.isnull(value):
        expected = ignore_missing
    elif isinstance(value, str):
        expected = False
    elif isinstance(value, (int, float)):
        expected = True
    else:
        expected = False
    
    assert result == expected, f"dtype validation failed for {value} (type: {type(value).__name__})"


# Test edge case: Range validation with inverted range
def test_inverted_range():
    """Test range validation when min > max."""
    # This tests what happens with an invalid range
    validator = column_range_validation_factory(100, 50)  # min > max
    
    # Nothing should be valid in an inverted range
    result, _ = validator(75)  # Between the numbers but range is inverted
    assert result == False, "Value between inverted range bounds should fail"
    
    result, _ = validator(25)  # Below both
    assert result == False, "Value below inverted range should fail"
    
    result, _ = validator(125)  # Above both
    assert result == False, "Value above inverted range should fail"


# Test edge case: Extreme numeric ranges  
def test_extreme_numeric_ranges():
    """Test range validation with system max/min values."""
    import sys as sys_module
    
    # Test with no min specified (should use system min)
    validator_no_min = column_range_validation_factory(None, 0)
    result, _ = validator_no_min(-sys_module.maxsize)
    assert result == True, "System min value should pass when no min specified"
    
    # Test with no max specified (should use system max)
    validator_no_max = column_range_validation_factory(0, None)
    result, _ = validator_no_max(sys_module.maxsize - 1)
    assert result == True, "Near system max value should pass when no max specified"


# Test MultiColumnConstraintWithMetadata with conflicting validators
def test_multi_column_conflicting_validators():
    """Test MultiColumnConstraintWithMetadata with validators that conflict."""
    
    # Create validators that can't both be true
    range_validator = column_range_validation_factory(0, 10)
    category_validator = categorical_column_validator_factory([20, 30, 40])
    
    # Apply both to the same column - nothing can satisfy both
    validator = MultiColumnConstraintWithMetadata(
        "Conflicting validators test",
        {'value': [range_validator, category_validator]},
        ColumnWithMetadataException,
        raise_or_typecheck=False
    )
    
    # Test with values in range [0,10]
    df1 = pd.DataFrame({'value': [5, 7, 9]})
    result1 = validator.validate(df1)
    assert result1.success == False, "Values in range but not in categories should fail"
    
    # Test with values in categories
    df2 = pd.DataFrame({'value': [20, 30, 40]})
    result2 = validator.validate(df2)
    assert result2.success == False, "Values in categories but not in range should fail"


# Test property: Categorical validator with duplicate categories
@given(
    base_categories=st.lists(st.integers(min_value=0, max_value=10), min_size=1, max_size=5),
    test_val=st.integers(min_value=0, max_value=10)
)
def test_categorical_with_duplicates(base_categories, test_val):
    """Test that duplicate categories are handled correctly (should work like a set)."""
    # Create categories with duplicates
    categories_with_dups = base_categories + base_categories  # Double the list
    
    validator = categorical_column_validator_factory(categories_with_dups)
    result, _ = validator(test_val)
    
    # Should work like a set - duplicates don't matter
    expected = test_val in set(base_categories)
    assert result == expected, f"Categorical validation with duplicates failed"


# Test NaN and infinity handling in range validation
def test_special_float_values_in_range():
    """Test how range validation handles NaN and infinity."""
    validator = column_range_validation_factory(0, 100, ignore_missing_vals=False)
    
    # Test NaN
    result_nan, _ = validator(float('nan'))
    assert result_nan == False, "NaN should fail range validation"
    
    # Test infinity
    result_inf, _ = validator(float('inf'))
    assert result_inf == False, "Infinity should fail range validation (above max)"
    
    result_neg_inf, _ = validator(float('-inf'))
    assert result_neg_inf == False, "Negative infinity should fail range validation (below min)"
    
    # With ignore_missing_vals=True, NaN should pass
    validator_ignore = column_range_validation_factory(0, 100, ignore_missing_vals=True)
    result_nan_ignore, _ = validator_ignore(float('nan'))
    assert result_nan_ignore == True, "NaN should pass when ignore_missing_vals=True"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])