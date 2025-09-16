"""Investigate the join ambiguity issue in SQLAlchemy."""

from sqlalchemy import Column, Integer, String, Table, MetaData, ForeignKey
from sqlalchemy.future import select
from sqlalchemy.exc import InvalidRequestError


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


def test_multiple_joins_issue():
    """Reproduce the join ambiguity issue."""
    print("Test 1: Multiple tables in select with chained joins")
    print("=" * 60)
    
    # This is what failed - selecting from multiple tables and trying to join
    try:
        stmt = select(users, posts, comments).join(posts).join(comments)
        compiled = str(stmt.compile())
        print("SUCCESS: Query compiled")
        print(f"SQL: {compiled}")
    except InvalidRequestError as e:
        print(f"ERROR: {e}")
        print("\nThis error occurs because SQLAlchemy can't determine which")
        print("table to join FROM when multiple tables are in the SELECT.")
    
    print("\n" + "=" * 60)
    print("Test 2: Using select_from() to specify explicit left side")
    
    # The correct way - using select_from to be explicit
    try:
        stmt = select(users, posts, comments).select_from(users).join(posts).join(comments)
        compiled = str(stmt.compile())
        print("SUCCESS: Query compiled with select_from()")
        print(f"SQL: {compiled[:200]}...")
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("Test 3: Selecting from single table with joins (implicit left side)")
    
    # This should work - single table in FROM, joins are unambiguous
    try:
        stmt = select(users).join(posts).join(comments)
        compiled = str(stmt.compile())
        print("SUCCESS: Query compiled with single table")
        print(f"SQL: {compiled[:200]}...")
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("Test 4: Join with explicit ON clause")
    
    # Providing explicit ON clause might help
    try:
        stmt = select(users, posts).join(posts, users.c.id == posts.c.user_id)
        compiled = str(stmt.compile())
        print("SUCCESS: Query compiled with explicit ON clause")
        print(f"SQL: {compiled[:200]}...")
    except InvalidRequestError as e:
        print(f"ERROR: {e}")
        print("Even with explicit ON clause, multiple tables in SELECT causes ambiguity")
    
    print("\n" + "=" * 60)
    print("Test 5: Documentation check")
    print("From the error message, this appears to be EXPECTED behavior.")
    print("SQLAlchemy requires explicit left side when multiple tables in SELECT.")
    print("This is a design decision to prevent ambiguity, not a bug.")
    
    return True


def test_minimal_reproduction():
    """Minimal test case for the issue."""
    print("\nMinimal Reproduction:")
    print("=" * 60)
    
    # Simplest case that reproduces the issue
    metadata = MetaData()
    t1 = Table('t1', metadata, Column('id', Integer, primary_key=True))
    t2 = Table('t2', metadata, Column('id', Integer, primary_key=True))
    
    try:
        # Multiple tables in select, then join - ambiguous
        stmt = select(t1, t2).join(t2)
        compiled = str(stmt.compile())
        print("Unexpected: This compiled successfully")
    except InvalidRequestError as e:
        print("Expected InvalidRequestError:")
        print(str(e)[:200])
        
        # The fix - be explicit about the FROM clause
        stmt_fixed = select(t1, t2).select_from(t1).join(t2, t1.c.id == t2.c.id)
        print("\nFixed version with select_from():")
        print(f"SQL: {str(stmt_fixed.compile())}")


if __name__ == "__main__":
    test_multiple_joins_issue()
    test_minimal_reproduction()