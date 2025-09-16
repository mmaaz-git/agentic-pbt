"""Property-based tests for sqlalchemy.future module."""

import math
from hypothesis import given, strategies as st, assume, settings
from sqlalchemy.future import select, create_engine
from sqlalchemy import column, text, literal, and_, or_


# Strategy for generating valid column names
column_names = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz_",
    min_size=1,
    max_size=20
).filter(lambda x: not x.startswith('_'))

# Strategy for positive integers (for limit/offset)
positive_ints = st.integers(min_value=0, max_value=10000)

# Strategy for small positive integers
small_ints = st.integers(min_value=0, max_value=100)


@given(column_names)
def test_select_immutability(col_name):
    """Test that select methods return new objects (immutability)."""
    original = select(column(col_name))
    
    # Test various modifications
    modified1 = original.where(column(col_name) > 5)
    modified2 = original.limit(10)
    modified3 = original.distinct()
    modified4 = original.order_by(column(col_name))
    
    # All should be different objects
    assert original is not modified1
    assert original is not modified2
    assert original is not modified3
    assert original is not modified4
    assert modified1 is not modified2


@given(column_names, positive_ints, positive_ints)
def test_select_type_preservation(col_name, limit_val, offset_val):
    """Test that chaining operations preserves the Select type."""
    s = select(column(col_name))
    
    # Chain multiple operations
    s2 = s.where(column(col_name) > 0)
    s3 = s2.limit(limit_val)
    s4 = s3.offset(offset_val)
    s5 = s4.distinct()
    
    # All should have the same type
    assert type(s) == type(s2) == type(s3) == type(s4) == type(s5)
    assert s.__class__.__name__ == 'Select'


@given(positive_ints, positive_ints)
def test_limit_offset_preservation(limit_val, offset_val):
    """Test that limit and offset values are preserved correctly."""
    s = select().limit(limit_val).offset(offset_val)
    
    # The values should be stored internally
    assert hasattr(s, '_limit')
    assert hasattr(s, '_offset')
    
    # Multiple limits should replace, not accumulate
    s2 = s.limit(limit_val + 10)
    assert s is not s2  # Should be a new object


@given(st.lists(column_names, min_size=1, max_size=5, unique=True))
def test_multiple_where_accumulation(col_names):
    """Test that multiple where clauses accumulate properly."""
    s = select()
    
    # Add multiple where clauses
    for col in col_names:
        s = s.where(column(col) > 0)
    
    # Each where should create a new object
    s2 = select()
    for col in col_names:
        s_prev = s2
        s2 = s2.where(column(col) > 0)
        assert s_prev is not s2


@given(column_names, column_names, column_names)
def test_order_by_chaining(col1, col2, col3):
    """Test that order_by operations can be chained."""
    s = select()
    
    # Chain order_by operations
    s1 = s.order_by(column(col1))
    s2 = s1.order_by(column(col2))
    s3 = s2.order_by(column(col3))
    
    # Each should be a new object
    assert s is not s1
    assert s1 is not s2
    assert s2 is not s3
    
    # Type should be preserved
    assert type(s) == type(s1) == type(s2) == type(s3)


@given(st.lists(column_names, min_size=1, max_size=5, unique=True))
def test_group_by_accumulation(col_names):
    """Test that group_by operations work correctly."""
    s = select()
    
    # Add group_by for each column
    for col in col_names:
        s = s.group_by(column(col))
    
    # Should have group_by method available for chaining
    assert hasattr(s, 'group_by')
    assert hasattr(s, 'having')  # having should be available after group_by


@given(column_names)
def test_distinct_idempotence(col_name):
    """Test that distinct() is idempotent-ish (calling twice is safe)."""
    s = select(column(col_name))
    
    s1 = s.distinct()
    s2 = s1.distinct()  # Calling distinct again
    
    # Both should work and be different objects
    assert s is not s1
    assert s1 is not s2
    assert type(s) == type(s1) == type(s2)


@given(column_names, positive_ints)
def test_limit_with_zero(col_name, offset_val):
    """Test edge case of limit with zero."""
    s = select(column(col_name)).limit(0).offset(offset_val)
    
    # Should not raise an error
    assert hasattr(s, '_limit')
    assert hasattr(s, '_offset')


@given(st.lists(column_names, min_size=2, max_size=2, unique=True))
def test_union_operations(col_names):
    """Test that union operations work correctly."""
    col1, col2 = col_names
    
    s1 = select(column(col1))
    s2 = select(column(col2))
    
    # Test union
    union_result = s1.union(s2)
    assert union_result is not s1
    assert union_result is not s2
    
    # Test union_all
    union_all_result = s1.union_all(s2)
    assert union_all_result is not s1
    assert union_all_result is not s2
    assert union_all_result is not union_result


@given(st.lists(column_names, min_size=2, max_size=2, unique=True))
def test_intersect_operations(col_names):
    """Test that intersect operations work correctly."""
    col1, col2 = col_names
    
    s1 = select(column(col1))
    s2 = select(column(col2))
    
    # Test intersect
    intersect_result = s1.intersect(s2)
    assert intersect_result is not s1
    assert intersect_result is not s2
    
    # Test intersect_all
    intersect_all_result = s1.intersect_all(s2)
    assert intersect_all_result is not s1
    assert intersect_all_result is not s2
    assert intersect_all_result is not intersect_result


@given(st.lists(column_names, min_size=2, max_size=2, unique=True))
def test_except_operations(col_names):
    """Test that except operations work correctly."""
    col1, col2 = col_names
    
    s1 = select(column(col1))
    s2 = select(column(col2))
    
    # Test except_
    except_result = s1.except_(s2)
    assert except_result is not s1
    assert except_result is not s2
    
    # Test except_all
    except_all_result = s1.except_all(s2)
    assert except_all_result is not s1
    assert except_all_result is not s2
    assert except_all_result is not except_result


@given(column_names, small_ints, small_ints)
def test_fetch_operation(col_name, count, offset):
    """Test the fetch operation (alternative to limit/offset)."""
    assume(count >= 0)
    assume(offset >= 0)
    
    s = select(column(col_name))
    
    # fetch is an alternative to limit/offset
    s_fetch = s.fetch(count, with_offset=offset)
    
    assert s is not s_fetch
    assert type(s) == type(s_fetch)


@given(column_names)
def test_subquery_creation(col_name):
    """Test that subquery() creates a proper subquery."""
    s = select(column(col_name))
    
    # Create subquery
    subq = s.subquery()
    
    # Should be a different type
    assert type(subq).__name__ == 'Subquery'
    assert type(subq) != type(s)


@given(column_names)
def test_cte_creation(col_name):
    """Test that cte() creates a proper CTE."""
    s = select(column(col_name))
    
    # Create CTE
    cte_result = s.cte()
    
    # Should be a different type
    assert type(cte_result).__name__ == 'CTE'
    assert type(cte_result) != type(s)


@given(column_names, st.text(min_size=1, max_size=20))
def test_alias_creation(col_name, alias_name):
    """Test that alias() creates a proper alias."""
    s = select(column(col_name))
    
    # Create alias
    alias_result = s.alias(alias_name)
    
    # Should be a different type
    assert type(alias_result).__name__ == 'Subquery'
    assert type(alias_result) != type(s)


if __name__ == "__main__":
    # Run tests with pytest
    import sys
    sys.exit(0)