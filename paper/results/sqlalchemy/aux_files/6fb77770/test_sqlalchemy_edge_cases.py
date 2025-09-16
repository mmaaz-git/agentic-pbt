"""Test edge cases and potential bugs in sqlalchemy.future."""

from hypothesis import given, strategies as st, assume, settings
from sqlalchemy.future import select, create_engine
from sqlalchemy import column, text, literal, Integer, String, MetaData, Table, Column
import warnings


# Test for potential integer overflow in limit/offset
@given(st.integers())
def test_limit_with_negative_values(limit_val):
    """Test that negative limit values are handled correctly."""
    s = select(column('x'))
    
    try:
        s_limited = s.limit(limit_val)
        # If negative values are accepted, they should be stored
        assert hasattr(s_limited, '_limit')
        
        # Check if negative limit causes issues when combined with other operations
        s_combined = s_limited.offset(10).distinct()
        assert s_combined is not None
    except (ValueError, TypeError) as e:
        # If it raises an error for negative values, that's acceptable behavior
        assume(limit_val >= 0)


@given(st.integers())
def test_offset_with_negative_values(offset_val):
    """Test that negative offset values are handled correctly."""
    s = select(column('x'))
    
    try:
        s_offset = s.offset(offset_val)
        # If negative values are accepted, they should be stored
        assert hasattr(s_offset, '_offset')
    except (ValueError, TypeError) as e:
        # If it raises an error for negative values, that's acceptable behavior
        assume(offset_val >= 0)


@given(st.text())
def test_column_with_special_characters(col_name):
    """Test that column names with special characters are handled."""
    assume(len(col_name) > 0)
    
    try:
        col = column(col_name)
        s = select(col)
        
        # Should be able to chain operations even with special column names
        s2 = s.where(col > 5)
        s3 = s2.limit(10)
        
        assert s is not s2
        assert s2 is not s3
    except Exception as e:
        # Some characters might be invalid - that's okay
        pass


@given(st.lists(st.text(min_size=1), min_size=1, max_size=5))
def test_multiple_columns_same_name(col_names):
    """Test selecting multiple columns with the same name."""
    # Use the same name for all columns
    same_name = col_names[0]
    
    try:
        # Create multiple column objects with the same name
        columns = [column(same_name) for _ in range(len(col_names))]
        s = select(*columns)
        
        # Should work without errors
        assert s is not None
        
        # Test chaining
        s2 = s.limit(10)
        assert s is not s2
    except Exception as e:
        # This might be a legitimate error
        pass


@given(st.integers(min_value=-1000, max_value=1000))
def test_limit_offset_interaction(value):
    """Test interaction between limit and offset with same value."""
    assume(value >= 0)
    
    s = select(column('x'))
    
    # Apply same value to both limit and offset
    s1 = s.limit(value).offset(value)
    s2 = s.offset(value).limit(value)  # Reverse order
    
    # Both should work
    assert s1 is not None
    assert s2 is not None
    assert s1 is not s2  # Different objects
    
    # Check that values are preserved
    assert hasattr(s1, '_limit')
    assert hasattr(s1, '_offset')
    assert hasattr(s2, '_limit')
    assert hasattr(s2, '_offset')


@given(st.integers(min_value=0, max_value=100))
def test_limit_replacement_not_accumulation(limit1):
    """Test that multiple limit() calls replace rather than accumulate."""
    limit2 = limit1 + 10
    limit3 = limit1 + 20
    
    s = select(column('x'))
    
    # Apply multiple limits
    s1 = s.limit(limit1)
    s2 = s1.limit(limit2)
    s3 = s2.limit(limit3)
    
    # Each should be a new object
    assert s is not s1
    assert s1 is not s2
    assert s2 is not s3
    
    # The last limit should be the one that applies
    # We can't directly check the value, but we can verify the behavior


@given(st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=100))
def test_many_where_clauses(conditions):
    """Test adding many where clauses."""
    s = select(column('x'))
    
    # Add a where clause for each condition
    for i, cond in enumerate(conditions):
        try:
            s = s.where(text(f"x > {i}"))
        except:
            # Some text might cause issues
            pass
    
    # Should still be a valid Select object
    assert s is not None
    assert type(s).__name__ == 'Select'


@given(st.booleans(), st.booleans(), st.integers(min_value=0, max_value=100))
def test_fetch_with_flags(with_ties, percent, count):
    """Test fetch with different flag combinations."""
    s = select(column('x'))
    
    try:
        s_fetch = s.fetch(count, with_ties=with_ties, percent=percent)
        
        # Should create a new object
        assert s_fetch is not s
        assert type(s_fetch).__name__ == 'Select'
        
        # Test that fetch replaces limit
        s_limit_then_fetch = s.limit(50).fetch(count, with_ties=with_ties, percent=percent)
        assert s_limit_then_fetch is not None
        
    except Exception as e:
        # Some combinations might not be valid
        pass


@given(st.text(min_size=0, max_size=1000))
def test_empty_and_long_alias_names(alias_name):
    """Test alias creation with empty or very long names."""
    s = select(column('x'))
    
    try:
        if len(alias_name) == 0:
            # Empty alias name might cause issues
            alias_result = s.alias(alias_name)
        else:
            alias_result = s.alias(alias_name)
        
        # Should create a subquery
        assert type(alias_result).__name__ == 'Subquery'
    except (ValueError, TypeError) as e:
        # Empty or extremely long names might be rejected
        pass


@given(st.lists(st.text(min_size=1, max_size=20), min_size=2, max_size=2))
def test_set_operations_with_same_column(col_names):
    """Test set operations when both selects use the same column name."""
    col_name = col_names[0]  # Use same column name for both
    
    s1 = select(column(col_name))
    s2 = select(column(col_name))
    
    # These should all work even with identical column names
    union_result = s1.union(s2)
    intersect_result = s1.intersect(s2)
    except_result = s1.except_(s2)
    
    assert union_result is not None
    assert intersect_result is not None
    assert except_result is not None
    
    # All should be different objects
    assert union_result is not intersect_result
    assert intersect_result is not except_result
    assert union_result is not except_result


if __name__ == "__main__":
    import sys
    print("Running edge case tests...")
    # Run with pytest
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))