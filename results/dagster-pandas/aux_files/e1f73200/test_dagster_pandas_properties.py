import sys
import math
import pandas as pd
from hypothesis import given, strategies as st, assume, settings
import pytest

# Add the site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-pandas_env/lib/python3.13/site-packages/')

from dagster_pandas.constraints import (
    column_range_validation_factory,
    categorical_column_validator_factory,
    StrictColumnsWithMetadata,
    non_null_validation,
    dtype_in_set_validation_factory,
)


# Property 1: Range validation with boundaries
@given(
    min_val=st.integers(min_value=-1000, max_value=1000),
    max_val=st.integers(min_value=-1000, max_value=1000),
    test_val=st.integers(min_value=-2000, max_value=2000)
)
def test_range_validation_boundaries(min_val, max_val, test_val):
    """Test that range validation correctly identifies in-range and out-of-range values."""
    assume(min_val <= max_val)  # Ensure valid range
    
    validator = column_range_validation_factory(min_val, max_val)
    result, metadata = validator(test_val)
    
    # Property: value is valid iff it's within the range
    expected = min_val <= test_val <= max_val
    assert result == expected, f"Range [{min_val}, {max_val}] validation for {test_val} returned {result}, expected {expected}"


# Property 2: Range validation with nulls
@given(
    min_val=st.integers(min_value=-100, max_value=100),
    max_val=st.integers(min_value=-100, max_value=100),
    ignore_missing=st.booleans()
)
def test_range_validation_null_handling(min_val, max_val, ignore_missing):
    """Test that null handling in range validation respects ignore_missing_vals parameter."""
    assume(min_val <= max_val)
    
    validator = column_range_validation_factory(min_val, max_val, ignore_missing_vals=ignore_missing)
    result, metadata = validator(pd.NA)
    
    # Property: when ignore_missing_vals=True, nulls should pass; otherwise fail
    if ignore_missing:
        assert result == True, f"With ignore_missing_vals=True, null should pass validation"
    else:
        assert result == False, f"With ignore_missing_vals=False, null should fail validation"


# Property 3: Categorical validation set membership
@given(
    categories=st.sets(st.integers(min_value=0, max_value=100), min_size=1, max_size=20),
    test_val=st.integers(min_value=-10, max_value=110)
)
def test_categorical_validation_membership(categories, test_val):
    """Test that categorical validation correctly checks set membership."""
    validator = categorical_column_validator_factory(categories)
    result, metadata = validator(test_val)
    
    # Property: value is valid iff it's in the categories set
    expected = test_val in categories
    assert result == expected, f"Category validation for {test_val} in {categories} returned {result}, expected {expected}"


# Property 4: StrictColumnsWithMetadata ordering invariant
@given(
    column_list=st.lists(st.text(min_size=1, max_size=10, alphabet='abcdefghijk'), min_size=1, max_size=10, unique=True),
    shuffle_seed=st.integers(min_value=0, max_value=1000)
)
def test_strict_columns_ordering(column_list, shuffle_seed):
    """Test that StrictColumnsWithMetadata correctly validates column ordering."""
    import random
    
    # Create a dataframe with the exact columns
    df_correct = pd.DataFrame(columns=column_list)
    
    # Create a shuffled version
    shuffled_cols = column_list.copy()
    random.Random(shuffle_seed).shuffle(shuffled_cols)
    df_shuffled = pd.DataFrame(columns=shuffled_cols)
    
    # Test with enforce_ordering=True
    validator_strict = StrictColumnsWithMetadata(column_list, enforce_ordering=True, raise_or_typecheck=False)
    
    # Correct order should pass
    result_correct = validator_strict.validate(df_correct)
    assert result_correct.success == True, "Exact column order should pass with enforce_ordering=True"
    
    # Shuffled order should fail if order actually changed
    if shuffled_cols != column_list:
        result_shuffled = validator_strict.validate(df_shuffled)
        assert result_shuffled.success == False, f"Different column order should fail with enforce_ordering=True"
    
    # Test with enforce_ordering=False
    validator_loose = StrictColumnsWithMetadata(column_list, enforce_ordering=False, raise_or_typecheck=False)
    
    # Both should pass since columns are the same (just different order)
    result_correct_loose = validator_loose.validate(df_correct)
    assert result_correct_loose.success == True
    
    result_shuffled_loose = validator_loose.validate(df_shuffled)
    assert result_shuffled_loose.success == True, "Same columns in different order should pass with enforce_ordering=False"


# Property 5: StrictColumnsWithMetadata detects missing/extra columns
@given(
    required_cols=st.sets(st.text(min_size=1, max_size=5, alphabet='abcdefg'), min_size=2, max_size=5),
    extra_cols=st.sets(st.text(min_size=1, max_size=5, alphabet='hijklmn'), min_size=1, max_size=3),
    missing_count=st.integers(min_value=1, max_value=2)
)
def test_strict_columns_missing_extra_detection(required_cols, extra_cols, missing_count):
    """Test that StrictColumnsWithMetadata correctly identifies missing and extra columns."""
    assume(len(required_cols) > missing_count)  # Can't remove more cols than we have
    assume(len(required_cols & extra_cols) == 0)  # No overlap
    
    required_list = list(required_cols)
    
    # Create dataframe with some missing and some extra columns
    actual_cols = required_list[missing_count:]  # Remove some required
    actual_cols.extend(list(extra_cols))  # Add some extra
    df = pd.DataFrame(columns=actual_cols)
    
    validator = StrictColumnsWithMetadata(required_list, enforce_ordering=False, raise_or_typecheck=False)
    result = validator.validate(df)
    
    # Should fail because columns don't match
    assert result.success == False, f"Mismatched columns should fail validation"
    
    # Check that metadata correctly identifies the issues
    if hasattr(result, 'metadata') and result.metadata:
        constraint_meta = result.metadata.get('constraint_metadata')
        if constraint_meta and hasattr(constraint_meta, 'data'):
            actual_meta = constraint_meta.data.get('actual', {})
            
            # The missing columns should be reported
            if 'missing_columns' in actual_meta:
                missing_reported = set(actual_meta['missing_columns'])
                missing_expected = set(required_list[:missing_count])
                assert missing_reported == missing_expected, f"Missing columns mismatch: reported {missing_reported} vs expected {missing_expected}"


# Property 6: dtype validation type checking
@given(
    test_int=st.integers(),
    test_float=st.floats(allow_nan=False, allow_infinity=False),
    test_str=st.text(min_size=1, max_size=10)
)
def test_dtype_validation_type_checking(test_int, test_float, test_str):
    """Test that dtype validation correctly identifies types."""
    # Integer validator
    int_validator = dtype_in_set_validation_factory(int)
    assert int_validator(test_int)[0] == True, f"Integer {test_int} should pass int validator"
    assert int_validator(test_str)[0] == False, f"String '{test_str}' should fail int validator"
    
    # String validator  
    str_validator = dtype_in_set_validation_factory(str)
    assert str_validator(test_str)[0] == True, f"String '{test_str}' should pass str validator"
    assert str_validator(test_int)[0] == False, f"Integer {test_int} should fail str validator"
    
    # Multiple types validator
    num_validator = dtype_in_set_validation_factory((int, float))
    assert num_validator(test_int)[0] == True, f"Integer should pass (int, float) validator"
    assert num_validator(test_float)[0] == True, f"Float should pass (int, float) validator"
    assert num_validator(test_str)[0] == False, f"String should fail (int, float) validator"


# Property 7: Non-null validation
@given(
    value=st.one_of(
        st.integers(),
        st.floats(allow_nan=False),
        st.text(min_size=1),
        st.none()
    )
)
def test_non_null_validation(value):
    """Test that non_null_validation correctly identifies null values."""
    result, metadata = non_null_validation(value)
    
    # Using pandas null checking for consistency with the library
    is_null = pd.isnull(value)
    expected = not is_null
    
    assert result == expected, f"non_null_validation({value}) returned {result}, expected {expected} (is_null={is_null})"


if __name__ == "__main__":
    # Run with increased examples for more thorough testing
    pytest.main([__file__, "-v", "--tb=short"])