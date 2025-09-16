"""Final edge case tests looking for potential bugs in sqlalchemy.future."""

import pytest
from hypothesis import given, strategies as st, assume, settings
from sqlalchemy import Column, Integer, String, Table, MetaData, literal, null, func
from sqlalchemy.future import select
import sys


metadata = MetaData()
users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('age', Integer)
)


# Test limit/offset with extreme values and boundary conditions
@given(st.sampled_from([0, -1, sys.maxsize, sys.maxsize + 1, -sys.maxsize]))
def test_extreme_limit_values(value):
    """Test limit with extreme values including boundaries."""
    stmt = select(users)
    
    try:
        # Apply the limit
        stmt_with_limit = stmt.limit(value)
        
        # Check it's stored correctly
        assert stmt_with_limit._limit == value
        
        # Try to compile
        compiled = str(stmt_with_limit.compile())
        
        # For valid limits, should contain LIMIT
        if value >= 0:
            assert "LIMIT" in compiled
    except (OverflowError, ValueError, TypeError) as e:
        # Some values might cause errors
        print(f"Value {value} caused error: {e}")


# Test offset/limit interaction with None values
@given(
    st.one_of(st.none(), st.integers(min_value=0, max_value=100)),
    st.one_of(st.none(), st.integers(min_value=0, max_value=100))
)
def test_none_limit_offset(limit_val, offset_val):
    """Test limit/offset with None values mixed with integers."""
    stmt = select(users)
    
    # Apply limit and offset (possibly None)
    stmt = stmt.limit(limit_val).offset(offset_val)
    
    # Check values are stored correctly
    assert stmt._limit == limit_val
    assert stmt._offset == offset_val
    
    # Should compile successfully
    compiled = str(stmt.compile())
    
    # Check SQL generation
    if limit_val is not None and limit_val > 0:
        assert "LIMIT" in compiled
    if offset_val is not None and offset_val > 0:
        assert "OFFSET" in compiled


# Test distinct() called with None
def test_distinct_with_none():
    """Test distinct() with None as argument."""
    stmt = select(users)
    
    try:
        # Try passing None to distinct
        stmt_distinct = stmt.distinct(None)
        compiled = str(stmt_distinct.compile())
        # Should either ignore None or handle it gracefully
        assert "DISTINCT" in compiled
    except (TypeError, AttributeError) as e:
        # Might reject None - that's ok
        pass


# Test where with empty conditions
def test_where_with_empty_conditions():
    """Test where() with various empty/null conditions."""
    stmt = select(users)
    
    # Test with empty list unpacked
    stmt1 = stmt.where(*[])
    assert str(stmt1.compile()) == str(stmt.compile())
    
    # Test with multiple empty calls
    stmt2 = stmt.where().where().where()
    assert str(stmt2.compile()) == str(stmt.compile())


# Test select with literal values
def test_select_with_literals():
    """Test select with literal values instead of columns."""
    # Select literal values
    stmt = select(literal(1), literal("test"), literal(None))
    
    compiled = str(stmt.compile())
    assert "SELECT" in compiled
    # Should have the literal values
    assert "1" in compiled or "?" in compiled  # Might use parameters


# Test select mixing columns and literals
@given(st.integers())
def test_select_mixed_columns_literals(int_val):
    """Test select with mix of columns and literal values."""
    stmt = select(
        users.c.id,
        literal(int_val).label("literal_int"),
        users.c.name,
        null().label("null_val")
    )
    
    compiled = str(stmt.compile())
    assert "SELECT" in compiled
    assert "users.id" in compiled
    assert "users.name" in compiled


# Test where clause with literal True/False
def test_where_with_python_booleans():
    """Test where clause with Python boolean values."""
    stmt_true = select(users).where(True)
    stmt_false = select(users).where(False)
    
    # These should compile but might have warnings
    compiled_true = str(stmt_true.compile())
    compiled_false = str(stmt_false.compile())
    
    assert "WHERE" in compiled_true
    assert "WHERE" in compiled_false


# Test limit/offset with float values
@given(st.floats(min_value=0.0, max_value=100.0))
def test_limit_offset_with_floats(float_val):
    """Test if limit/offset accept float values."""
    stmt = select(users)
    
    try:
        # Try to set limit with float
        stmt_limit = stmt.limit(float_val)
        # If it works, check the value
        assert stmt_limit._limit == float_val or stmt_limit._limit == int(float_val)
    except (TypeError, ValueError) as e:
        # Might reject floats - that's valid
        pass
    
    try:
        # Try to set offset with float
        stmt_offset = stmt.offset(float_val)
        # If it works, check the value
        assert stmt_offset._offset == float_val or stmt_offset._offset == int(float_val)
    except (TypeError, ValueError) as e:
        # Might reject floats - that's valid
        pass


# Test chaining same method many times
@given(st.integers(min_value=10, max_value=100))
def test_excessive_method_chaining(chain_length):
    """Test chaining the same method excessively."""
    stmt = select(users)
    
    # Chain where() many times with different conditions
    for i in range(chain_length):
        stmt = stmt.where(users.c.id != i)
    
    # Should still compile
    compiled = str(stmt.compile())
    assert "WHERE" in compiled
    
    # Check that all conditions are present
    # Due to AND chaining, might be complex
    assert stmt.whereclause is not None


# Test order_by with None
def test_order_by_with_none():
    """Test order_by() with None."""
    stmt = select(users)
    
    try:
        stmt_ordered = stmt.order_by(None)
        # If it accepts None, should either ignore it or reset ordering
        compiled = str(stmt_ordered.compile())
        # Might or might not have ORDER BY
        assert "SELECT" in compiled
    except (TypeError, AttributeError):
        # Rejecting None is valid
        pass


# Test group_by with duplicate columns
def test_group_by_duplicates():
    """Test group_by with duplicate column specifications."""
    stmt = select(users.c.age, func.count()).group_by(
        users.c.age,
        users.c.age,  # Duplicate
        users.c.age   # Another duplicate
    )
    
    compiled = str(stmt.compile())
    assert "GROUP BY" in compiled
    # Should handle duplicates gracefully


# Test having without group_by
def test_having_without_group_by():
    """Test having clause without group_by."""
    from sqlalchemy import func
    
    try:
        stmt = select(users).having(func.count() > 1)
        compiled = str(stmt.compile())
        # Some databases allow HAVING without GROUP BY
        assert "HAVING" in compiled
    except Exception:
        # Might require GROUP BY first
        pass


# Test fetch() as alternative to limit()
@given(st.integers(min_value=1, max_value=100))
def test_fetch_method(count):
    """Test fetch() method as alternative to limit()."""
    stmt = select(users)
    
    if hasattr(stmt, 'fetch'):
        stmt_fetch = stmt.fetch(count)
        compiled = str(stmt_fetch.compile())
        # Should generate FETCH or LIMIT
        assert "FETCH" in compiled or "LIMIT" in compiled
        
        # fetch() should replace limit()
        stmt_both = stmt.limit(10).fetch(count)
        assert "FETCH" in str(stmt_both.compile()) or str(count) in str(stmt_both.compile())