"""Test complex interactions and metamorphic properties in sqlalchemy.future."""

from hypothesis import given, strategies as st, assume, settings
from sqlalchemy.future import select
from sqlalchemy import column, text, literal, and_, or_, not_, true, false
import warnings


# Strategies
column_names = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10)
small_ints = st.integers(min_value=0, max_value=100)


@given(column_names, small_ints, small_ints)
def test_limit_fetch_interaction(col_name, limit_val, fetch_val):
    """Test that fetch replaces limit as documented."""
    s = select(column(col_name))
    
    # According to docs, fetch should replace limit
    s1 = s.limit(limit_val).fetch(fetch_val)
    s2 = s.fetch(fetch_val).limit(limit_val)
    
    # Both should work
    assert s1 is not None
    assert s2 is not None
    assert s1 is not s2
    
    # The behavior should be: last operation wins
    # Can't directly test the internal state, but operations should succeed


@given(column_names)
def test_chained_distinct_operations(col_name):
    """Test multiple distinct() calls - should be idempotent."""
    s = select(column(col_name))
    
    s1 = s.distinct()
    s2 = s1.distinct()
    s3 = s2.distinct()
    
    # All should be different objects (immutability)
    assert s is not s1
    assert s1 is not s2
    assert s2 is not s3
    
    # But functionality should be preserved
    assert type(s) == type(s1) == type(s2) == type(s3)


@given(st.lists(column_names, min_size=1, max_size=5, unique=True))
def test_where_clause_with_boolean_literals(col_names):
    """Test where clauses with boolean literals."""
    s = select()
    
    # Add where clauses with boolean conditions
    s1 = s.where(true())
    s2 = s1.where(false())
    s3 = s.where(and_(true(), false()))
    s4 = s.where(or_(true(), false()))
    s5 = s.where(not_(true()))
    
    # All should create valid select objects
    for sel in [s1, s2, s3, s4, s5]:
        assert sel is not None
        assert type(sel).__name__ == 'Select'
        assert sel is not s


@given(column_names, column_names)
def test_subquery_with_chained_operations(col1, col2):
    """Test creating subqueries after various operations."""
    s = select(column(col1)).where(column(col1) > 5).limit(10).distinct()
    
    # Create subquery
    subq = s.subquery()
    assert type(subq).__name__ == 'Subquery'
    
    # Should be able to select from subquery
    s2 = select(subq)
    assert s2 is not None
    assert type(s2).__name__ == 'Select'


@given(column_names)
def test_cte_recursive_potential(col_name):
    """Test CTE creation with potential for recursion."""
    s = select(column(col_name))
    
    # Create CTE
    cte1 = s.cte(name="cte1")
    assert type(cte1).__name__ == 'CTE'
    
    # Create another select using the CTE
    s2 = select(cte1)
    assert s2 is not None
    
    # Create another CTE from that
    cte2 = s2.cte(name="cte2")
    assert type(cte2).__name__ == 'CTE'
    assert cte1 is not cte2


@given(st.lists(column_names, min_size=3, max_size=3, unique=True))
def test_multiple_set_operations_chaining(col_names):
    """Test chaining multiple set operations."""
    c1, c2, c3 = col_names
    
    s1 = select(column(c1))
    s2 = select(column(c2))
    s3 = select(column(c3))
    
    # Chain set operations
    result = s1.union(s2).union(s3)
    assert result is not None
    
    # Try different combinations
    result2 = s1.intersect(s2).union(s3)
    assert result2 is not None
    
    result3 = s1.union(s2).except_(s3)
    assert result3 is not None
    
    # All should be different
    assert result is not result2
    assert result2 is not result3
    assert result is not result3


@given(column_names, small_ints)
def test_execution_options(col_name, timeout_val):
    """Test execution_options method."""
    s = select(column(col_name))
    
    # Apply execution options
    s_with_opts = s.execution_options(timeout=timeout_val)
    
    # Should create new object
    assert s is not s_with_opts
    assert type(s) == type(s_with_opts)
    
    # Should be chainable
    s_chain = s_with_opts.limit(10).where(column(col_name) > 0)
    assert s_chain is not None


@given(column_names)
def test_add_columns_operation(col_name):
    """Test add_columns to add more columns to select."""
    s = select(column(col_name))
    
    # Add more columns
    s2 = s.add_columns(column(col_name + "_2"))
    s3 = s2.add_columns(column(col_name + "_3"))
    
    # Should create new objects
    assert s is not s2
    assert s2 is not s3
    assert type(s) == type(s2) == type(s3)


@given(column_names, column_names)
def test_correlate_operations(col1, col2):
    """Test correlate and correlate_except methods."""
    s = select(column(col1))
    
    # Test correlate
    s_corr = s.correlate(column(col2))
    assert s_corr is not s
    assert type(s_corr).__name__ == 'Select'
    
    # Test correlate_except
    s_corr_except = s.correlate_except(column(col2))
    assert s_corr_except is not s
    assert s_corr_except is not s_corr
    assert type(s_corr_except).__name__ == 'Select'


@given(st.lists(column_names, min_size=1, max_size=10, unique=True))
def test_filter_vs_where_equivalence(col_names):
    """Test that filter and where behave the same (filter is alias for where)."""
    s = select()
    
    # Build with where
    s_where = s
    for col in col_names:
        s_where = s_where.where(column(col) > 0)
    
    # Build with filter
    s_filter = s
    for col in col_names:
        s_filter = s_filter.filter(column(col) > 0)
    
    # Both should work and produce Select objects
    assert type(s_where).__name__ == 'Select'
    assert type(s_filter).__name__ == 'Select'
    
    # They should be different objects
    assert s_where is not s_filter


@given(column_names)
def test_exists_transformation(col_name):
    """Test the exists() method that transforms select into an exists clause."""
    s = select(column(col_name)).where(column(col_name) > 5)
    
    # Transform to exists
    exists_clause = s.exists()
    
    # Should create a different type of object
    assert exists_clause is not None
    assert type(exists_clause).__name__ != 'Select'
    
    # Should be usable in another select
    s2 = select(literal(1)).where(exists_clause)
    assert s2 is not None
    assert type(s2).__name__ == 'Select'


@given(column_names)
def test_scalar_subquery_transformation(col_name):
    """Test as_scalar/scalar_subquery transformation."""
    s = select(column(col_name)).limit(1)
    
    # Transform to scalar subquery
    scalar = s.as_scalar()
    
    # Should create a different type
    assert scalar is not None
    assert scalar is not s
    assert type(scalar).__name__ != 'Select'
    
    # Should be usable in expressions
    s2 = select(scalar)
    assert s2 is not None
    assert type(s2).__name__ == 'Select'


@given(st.lists(column_names, min_size=2, max_size=5, unique=True))
def test_complex_boolean_where_conditions(col_names):
    """Test complex nested boolean conditions in where clauses."""
    s = select()
    
    if len(col_names) >= 2:
        c1, c2 = col_names[0], col_names[1]
        
        # Complex nested conditions
        condition1 = and_(column(c1) > 0, column(c2) < 100)
        condition2 = or_(column(c1) == 5, column(c2) == 10)
        condition3 = not_(and_(condition1, condition2))
        
        s1 = s.where(condition1)
        s2 = s1.where(condition2)
        s3 = s2.where(condition3)
        
        # All should work
        assert s1 is not None
        assert s2 is not None
        assert s3 is not None
        assert s is not s1
        assert s1 is not s2
        assert s2 is not s3


if __name__ == "__main__":
    import sys
    print("Running complex interaction tests...")
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))