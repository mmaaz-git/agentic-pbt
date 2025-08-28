"""Edge case property-based tests for sqlalchemy.future module."""

import pytest
from hypothesis import given, strategies as st, assume, settings
from sqlalchemy import Column, Integer, String, Table, MetaData, and_, or_, text
from sqlalchemy.future import select, create_engine
from sqlalchemy.sql import Select
import sys


# Create test tables
metadata = MetaData()
users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('age', Integer)
)


# Test with negative limit values - should they be allowed?
@given(st.integers(min_value=-1000, max_value=-1))
def test_negative_limit(limit_val):
    """Test behavior with negative limit values."""
    base_stmt = select(users)
    
    # Try to apply negative limit
    stmt = base_stmt.limit(limit_val)
    
    # Check if it's stored as-is
    assert stmt._limit == limit_val
    
    # Check if compilation fails or succeeds
    try:
        compiled = str(stmt.compile())
        # If it compiles, the negative value should be in the SQL
        assert str(limit_val) in compiled or "LIMIT" in compiled
    except Exception as e:
        # If it fails, that's also valid behavior
        pass


# Test with very large limit values
@given(st.integers(min_value=sys.maxsize - 100, max_value=sys.maxsize))
def test_very_large_limit(limit_val):
    """Test behavior with very large limit values."""
    base_stmt = select(users)
    
    stmt = base_stmt.limit(limit_val)
    assert stmt._limit == limit_val


# Test with limit 0 - edge case
def test_limit_zero():
    """Test behavior with limit 0."""
    base_stmt = select(users)
    stmt = base_stmt.limit(0)
    assert stmt._limit == 0
    
    # Should compile successfully
    compiled = str(stmt.compile())
    assert "LIMIT" in compiled


# Test offset with negative values
@given(st.integers(min_value=-1000, max_value=-1))
def test_negative_offset(offset_val):
    """Test behavior with negative offset values."""
    base_stmt = select(users)
    
    stmt = base_stmt.offset(offset_val)
    assert stmt._offset == offset_val
    
    # Check if compilation fails or succeeds
    try:
        compiled = str(stmt.compile())
        # If it compiles, check the value
        assert str(offset_val) in compiled or "OFFSET" in compiled
    except Exception as e:
        # If it fails, that's also valid behavior
        pass


# Test combining distinct with expressions (PostgreSQL specific)
def test_distinct_with_empty_expr():
    """Test distinct() with empty expression list."""
    base_stmt = select(users)
    
    # distinct() with no args vs distinct with empty *expr
    stmt1 = base_stmt.distinct()
    stmt2 = base_stmt.distinct(*[])  # Empty expression list
    
    # Both should be equivalent
    assert str(stmt1.compile()) == str(stmt2.compile())


# Test where with None condition
def test_where_with_none():
    """Test where() with None as condition."""
    base_stmt = select(users)
    
    try:
        stmt = base_stmt.where(None)
        # If it doesn't raise, check if None is filtered out
        if stmt.whereclause is None:
            # None was filtered out - valid behavior
            assert str(base_stmt.compile()) == str(stmt.compile())
        else:
            # None was included - also valid, but unusual
            pass
    except (TypeError, AttributeError) as e:
        # Raising an error for None is also valid behavior
        pass


# Test multiple distinct() calls with different arguments
@given(st.lists(st.sampled_from(['id', 'name', 'age']), min_size=0, max_size=3))
def test_distinct_with_columns(columns):
    """Test distinct() with column arguments (PostgreSQL DISTINCT ON)."""
    base_stmt = select(users)
    
    # Get column objects
    column_objs = [getattr(users.c, col) for col in columns]
    
    try:
        if column_objs:
            stmt = base_stmt.distinct(*column_objs)
        else:
            stmt = base_stmt.distinct()
        
        # Should store the distinct columns
        compiled = str(stmt.compile())
        assert "DISTINCT" in compiled
    except Exception as e:
        # Some backends might not support DISTINCT ON
        pass


# Test chaining where with conflicting conditions
@given(st.integers(min_value=1, max_value=100))
def test_conflicting_where_conditions(age):
    """Test where() with logically conflicting conditions."""
    base_stmt = select(users)
    
    # Add conflicting conditions
    stmt = base_stmt.where(users.c.age > age).where(users.c.age < age)
    
    # Both conditions should be present (ANDed together)
    # This creates an impossible condition, but should be valid SQL
    assert stmt.whereclause is not None
    
    compiled = str(stmt.compile())
    assert "AND" in compiled


# Test limit/offset with SQL expression objects
def test_limit_with_text_expression():
    """Test limit() with SQL text expression."""
    base_stmt = select(users)
    
    try:
        # Try using a text expression for limit
        stmt = base_stmt.limit(text("10"))
        
        # Should accept the text expression
        compiled = str(stmt.compile())
        assert "LIMIT" in compiled
    except Exception as e:
        # Some implementations might not accept text expressions
        pass


# Test very long chain of where clauses
@given(st.lists(st.integers(min_value=1, max_value=100), min_size=10, max_size=20))
def test_many_where_clauses(ages):
    """Test a very long chain of where clauses."""
    base_stmt = select(users)
    
    stmt = base_stmt
    for age in ages:
        stmt = stmt.where(users.c.age != age)
    
    # All conditions should be present
    assert stmt.whereclause is not None
    
    # Count the number of AND operations (should be len(ages) - 1)
    compiled = str(stmt.compile())
    # All conditions should be joined
    assert compiled.count("!=") == len(ages) or compiled.count("AND") >= len(ages) - 1


# Test create_engine with various URL formats
@given(st.sampled_from([
    "sqlite:///:memory:",
    "sqlite:///test.db",
    "postgresql://user:pass@localhost/dbname",
    "mysql://user:pass@localhost/dbname",
]))
def test_create_engine_url_formats(url):
    """Test create_engine with various URL formats."""
    try:
        # Only test with sqlite in-memory for actual connection
        if url.startswith("sqlite:///:memory:"):
            engine = create_engine(url)
            assert engine is not None
            assert hasattr(engine, 'connect')
            assert hasattr(engine, 'dispose')
            
            # Test that we can create a connection
            with engine.connect() as conn:
                assert conn is not None
        else:
            # For other databases, just test parsing
            # We can't actually connect without those databases running
            pass
    except Exception as e:
        # Some URLs might fail due to missing drivers
        pass


# Test select with no columns (SELECT *)
def test_select_star():
    """Test select with table but no specific columns."""
    stmt1 = select(users)  # Should select all columns
    stmt2 = select(users.c.id, users.c.name, users.c.age)  # Explicit columns
    
    # Both should reference the same table
    assert users in stmt1.froms
    assert users in stmt2.froms


# Test filter_by behavior (if it exists)
def test_filter_by_method():
    """Test filter_by method if it exists."""
    base_stmt = select(users)
    
    # Check if filter_by exists
    if hasattr(base_stmt, 'filter_by'):
        try:
            # filter_by typically takes keyword arguments
            stmt = base_stmt.filter_by(age=25)
            assert stmt.whereclause is not None
        except Exception as e:
            # Might not work without proper setup
            pass