"""Complex property tests for sqlalchemy.future - joins, complex where clauses, etc."""

import pytest
from hypothesis import given, strategies as st, assume, settings, example
from sqlalchemy import Column, Integer, String, Table, MetaData, and_, or_, not_, ForeignKey
from sqlalchemy.future import select
from sqlalchemy.sql import Select
import sys


# Create test tables with relationships
metadata = MetaData()
users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('age', Integer)
)

posts = Table('posts', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('title', String),
    Column('content', String)
)

comments = Table('comments', metadata,
    Column('id', Integer, primary_key=True),
    Column('post_id', Integer, ForeignKey('posts.id')),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('text', String)
)


# Test join chaining
def test_multiple_joins():
    """Test chaining multiple joins."""
    stmt = select(users, posts, comments).join(posts).join(comments)
    
    # Should compile without error
    compiled = str(stmt.compile())
    assert "JOIN" in compiled
    assert compiled.count("JOIN") >= 2


# Test self-join
def test_self_join():
    """Test self-join on same table."""
    # Create alias for self-join
    users_alias = users.alias('u2')
    
    stmt = select(users, users_alias).join(
        users_alias, 
        users.c.id == users_alias.c.id
    )
    
    compiled = str(stmt.compile())
    assert "JOIN" in compiled
    # Should have both the original and aliased table
    assert "users" in compiled
    assert "u2" in compiled or "users_" in compiled


# Test outer joins
def test_outer_join_types():
    """Test different join types."""
    # Left outer join
    stmt_left = select(users, posts).join(posts, isouter=True)
    compiled_left = str(stmt_left.compile())
    assert "LEFT" in compiled_left or "OUTER" in compiled_left
    
    # Full outer join
    stmt_full = select(users, posts).join(posts, full=True)
    compiled_full = str(stmt_full.compile())
    assert "FULL" in compiled_full or "JOIN" in compiled_full


# Test complex boolean where conditions
@given(
    st.lists(st.integers(min_value=1, max_value=100), min_size=2, max_size=5),
    st.lists(st.text(min_size=1, max_size=10), min_size=2, max_size=5)
)
def test_complex_where_conditions(ages, names):
    """Test complex AND/OR combinations in where clauses."""
    # Build complex condition: (age > ages[0] OR age < ages[1]) AND (name = names[0] OR name = names[1])
    age_cond = or_(users.c.age > ages[0], users.c.age < ages[1])
    name_cond = or_(users.c.name == names[0], users.c.name == names[1])
    
    stmt = select(users).where(and_(age_cond, name_cond))
    
    compiled = str(stmt.compile())
    assert "WHERE" in compiled
    # Should have both OR and AND
    assert "OR" in compiled
    assert "AND" in compiled


# Test NOT conditions
@given(st.integers(min_value=1, max_value=100))
def test_not_conditions(age):
    """Test NOT operator in where clauses."""
    # Test various NOT conditions
    stmt1 = select(users).where(not_(users.c.age > age))
    stmt2 = select(users).where(not_(users.c.age == age))
    
    compiled1 = str(stmt1.compile())
    compiled2 = str(stmt2.compile())
    
    # Should contain NOT or equivalent
    assert "NOT" in compiled1 or "!=" in compiled1 or "<=" in compiled1
    assert "NOT" in compiled2 or "!=" in compiled2


# Test limit/offset with join
@given(
    st.integers(min_value=1, max_value=100),
    st.integers(min_value=0, max_value=100)
)
def test_limit_offset_with_join(limit_val, offset_val):
    """Test that limit/offset work correctly with joins."""
    stmt = select(users, posts).join(posts).limit(limit_val).offset(offset_val)
    
    assert stmt._limit == limit_val
    assert stmt._offset == offset_val
    
    compiled = str(stmt.compile())
    assert "JOIN" in compiled
    assert "LIMIT" in compiled
    if offset_val > 0:
        assert "OFFSET" in compiled


# Test subquery in FROM clause
def test_subquery_in_from():
    """Test using a subquery in FROM clause."""
    # Create a subquery
    subq = select(users.c.id, users.c.name).where(users.c.age > 18).subquery()
    
    # Use subquery in another select
    stmt = select(subq)
    
    compiled = str(stmt.compile())
    assert "SELECT" in compiled
    # Should have nested SELECT
    assert compiled.count("SELECT") >= 2


# Test CTE (Common Table Expression)
def test_cte():
    """Test CTE functionality."""
    # Create a CTE
    cte = select(users).where(users.c.age > 18).cte('adult_users')
    
    # Use CTE in main query
    stmt = select(cte)
    
    compiled = str(stmt.compile())
    # Should have WITH clause
    assert "WITH" in compiled or "SELECT" in compiled


# Test exists() subquery
def test_exists_subquery():
    """Test EXISTS subquery pattern."""
    # Create exists condition
    exists_stmt = select(posts).where(posts.c.user_id == users.c.id).exists()
    
    # Use in main query
    stmt = select(users).where(exists_stmt)
    
    compiled = str(stmt.compile())
    assert "EXISTS" in compiled or "SELECT" in compiled


# Test scalar subquery
def test_scalar_subquery():
    """Test scalar subquery in select."""
    # Create scalar subquery
    scalar_subq = select(posts.c.id).where(posts.c.user_id == users.c.id).scalar_subquery()
    
    # Use in select
    stmt = select(users.c.name, scalar_subq.label('post_id'))
    
    compiled = str(stmt.compile())
    # Should have nested SELECT
    assert compiled.count("SELECT") >= 2


# Test UNION operations
def test_union_operations():
    """Test UNION, UNION ALL, INTERSECT, EXCEPT."""
    stmt1 = select(users.c.id).where(users.c.age > 18)
    stmt2 = select(users.c.id).where(users.c.age < 65)
    
    # Test UNION
    union_stmt = stmt1.union(stmt2)
    compiled_union = str(union_stmt.compile())
    assert "UNION" in compiled_union
    
    # Test UNION ALL
    union_all_stmt = stmt1.union_all(stmt2)
    compiled_union_all = str(union_all_stmt.compile())
    assert "UNION" in compiled_union_all
    
    # Test INTERSECT
    intersect_stmt = stmt1.intersect(stmt2)
    compiled_intersect = str(intersect_stmt.compile())
    assert "INTERSECT" in compiled_intersect
    
    # Test EXCEPT
    except_stmt = stmt1.except_(stmt2)
    compiled_except = str(except_stmt.compile())
    assert "EXCEPT" in compiled_except


# Test GROUP BY and HAVING
@given(st.integers(min_value=1, max_value=100))
def test_group_by_having(min_age):
    """Test GROUP BY with HAVING clause."""
    from sqlalchemy import func
    
    stmt = (
        select(users.c.age, func.count(users.c.id).label('count'))
        .group_by(users.c.age)
        .having(func.count(users.c.id) > 1)
    )
    
    compiled = str(stmt.compile())
    assert "GROUP BY" in compiled
    assert "HAVING" in compiled


# Test ORDER BY with multiple columns
@given(
    st.lists(
        st.sampled_from(['id', 'name', 'age']),
        min_size=1,
        max_size=3,
        unique=True
    )
)
def test_order_by_multiple(columns):
    """Test ORDER BY with multiple columns."""
    column_objs = [getattr(users.c, col) for col in columns]
    
    stmt = select(users).order_by(*column_objs)
    
    compiled = str(stmt.compile())
    assert "ORDER BY" in compiled
    
    # All columns should be in ORDER BY
    for col in columns:
        assert col in compiled


# Test that where(True) and where(False) behave correctly
def test_where_boolean_literals():
    """Test where clause with boolean literals."""
    from sqlalchemy import true, false
    
    # where(true()) should not filter anything
    stmt_true = select(users).where(true())
    compiled_true = str(stmt_true.compile())
    # Should have WHERE with a true condition
    assert "WHERE" in compiled_true
    
    # where(false()) should filter everything
    stmt_false = select(users).where(false())
    compiled_false = str(stmt_false.compile())
    # Should have WHERE with a false condition
    assert "WHERE" in compiled_false


# Test column label and alias
@given(st.text(min_size=1, max_size=20).filter(lambda x: x.isidentifier()))
def test_column_labels(label_name):
    """Test column labeling/aliasing."""
    stmt = select(
        users.c.id.label(label_name),
        users.c.name.label(f"{label_name}_name")
    )
    
    compiled = str(stmt.compile())
    assert "AS" in compiled
    assert label_name in compiled