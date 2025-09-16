"""Property-based tests for sqlalchemy.future module."""

import pytest
from hypothesis import given, strategies as st, assume, settings
from sqlalchemy import Column, Integer, String, Table, MetaData, and_, create_engine
from sqlalchemy.future import select
from sqlalchemy.sql import Select


# Create test tables
metadata = MetaData()
users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('age', Integer)
)

posts = Table('posts', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer),
    Column('title', String),
    Column('content', String)
)


# Test 1: distinct() is idempotent - applying it multiple times should give the same result
@given(st.integers(min_value=1, max_value=10))
def test_distinct_idempotent(num_applications):
    """Property: Applying distinct() multiple times should be idempotent."""
    base_stmt = select(users)
    
    # Apply distinct once
    stmt_once = base_stmt.distinct()
    
    # Apply distinct multiple times
    stmt_multiple = base_stmt
    for _ in range(num_applications):
        stmt_multiple = stmt_multiple.distinct()
    
    # Both should compile to the same SQL
    assert str(stmt_once.compile()) == str(stmt_multiple.compile())


# Test 2: limit() last value wins
@given(
    st.lists(st.integers(min_value=1, max_value=1000), min_size=1, max_size=10)
)
def test_limit_last_wins(limits):
    """Property: Applying multiple limits should result in the last limit being used."""
    base_stmt = select(users)
    
    # Apply all limits
    stmt = base_stmt
    for limit in limits:
        stmt = stmt.limit(limit)
    
    # Get the actual limit value from the compiled statement
    compiled = stmt.compile()
    
    # The Select object should have _limit with the last value
    assert stmt._limit == limits[-1]


# Test 3: offset() last value wins
@given(
    st.lists(st.integers(min_value=0, max_value=1000), min_size=1, max_size=10)
)
def test_offset_last_wins(offsets):
    """Property: Applying multiple offsets should result in the last offset being used."""
    base_stmt = select(users)
    
    # Apply all offsets
    stmt = base_stmt
    for offset in offsets:
        stmt = stmt.offset(offset)
    
    # The Select object should have _offset with the last value
    assert stmt._offset == offsets[-1]


# Test 4: Multiple where() clauses are cumulative
@given(
    st.lists(
        st.integers(min_value=1, max_value=100),
        min_size=2,
        max_size=5
    )
)
def test_where_cumulative(age_values):
    """Property: Multiple where() calls should be cumulative (AND logic)."""
    base_stmt = select(users)
    
    # Apply multiple where clauses
    stmt = base_stmt
    conditions = []
    for age in age_values:
        condition = users.c.age > age
        conditions.append(condition)
        stmt = stmt.where(condition)
    
    # The statement should contain all conditions ANDed together
    # Check by compiling and verifying the where clause
    compiled = stmt.compile()
    
    # The where clause should exist and contain all conditions
    assert stmt.whereclause is not None
    
    # Build expected combined condition manually
    expected_combined = and_(*conditions)
    
    # Compare the structures (both should produce equivalent SQL)
    assert str(stmt.whereclause.compile()) == str(expected_combined.compile())


# Test 5: Resetting limit with None
@given(
    st.integers(min_value=1, max_value=1000),
    st.integers(min_value=1, max_value=1000)
)
def test_limit_reset_with_none(first_limit, second_limit):
    """Property: Setting limit to None should reset it, allowing a new limit."""
    base_stmt = select(users)
    
    # Apply first limit
    stmt = base_stmt.limit(first_limit)
    assert stmt._limit == first_limit
    
    # Reset with None
    stmt = stmt.limit(None)
    assert stmt._limit is None
    
    # Apply second limit
    stmt = stmt.limit(second_limit)
    assert stmt._limit == second_limit


# Test 6: Resetting offset with None
@given(
    st.integers(min_value=0, max_value=1000),
    st.integers(min_value=0, max_value=1000)
)
def test_offset_reset_with_none(first_offset, second_offset):
    """Property: Setting offset to None should reset it, allowing a new offset."""
    base_stmt = select(users)
    
    # Apply first offset
    stmt = base_stmt.offset(first_offset)
    assert stmt._offset == first_offset
    
    # Reset with None
    stmt = stmt.offset(None)
    assert stmt._offset is None
    
    # Apply second offset
    stmt = stmt.offset(second_offset)
    assert stmt._offset == second_offset


# Test 7: filter() is a synonym for where()
@given(st.integers(min_value=1, max_value=100))
def test_filter_is_where_synonym(age_value):
    """Property: filter() should behave identically to where()."""
    base_stmt = select(users)
    
    condition = users.c.age > age_value
    
    # Apply using where
    stmt_where = base_stmt.where(condition)
    
    # Apply using filter  
    stmt_filter = base_stmt.filter(condition)
    
    # Both should compile to the same SQL
    assert str(stmt_where.compile()) == str(stmt_filter.compile())


# Test 8: Empty where() doesn't affect the statement
def test_empty_where():
    """Property: Calling where() with no arguments should not modify the statement."""
    base_stmt = select(users)
    stmt_with_empty_where = base_stmt.where()
    
    # Both should compile to the same SQL
    assert str(base_stmt.compile()) == str(stmt_with_empty_where.compile())


# Test 9: Chaining limit and offset preserves both
@given(
    st.integers(min_value=1, max_value=100),
    st.integers(min_value=0, max_value=100)
)
def test_limit_offset_chain(limit_val, offset_val):
    """Property: Chaining limit and offset should preserve both values."""
    base_stmt = select(users)
    
    # Chain limit and offset
    stmt = base_stmt.limit(limit_val).offset(offset_val)
    assert stmt._limit == limit_val
    assert stmt._offset == offset_val
    
    # Reverse order should also work
    stmt2 = base_stmt.offset(offset_val).limit(limit_val)
    assert stmt2._limit == limit_val
    assert stmt2._offset == offset_val