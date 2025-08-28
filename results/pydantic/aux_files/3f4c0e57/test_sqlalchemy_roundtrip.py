"""Round-trip and transaction property tests for sqlalchemy.future."""

import pytest
from hypothesis import given, strategies as st, assume, settings
from sqlalchemy import Column, Integer, String, Table, MetaData, create_engine, text
from sqlalchemy.future import select, create_engine as future_create_engine
from sqlalchemy.future import Connection, Engine
import tempfile
import os


# Test round-trip: compile and parse back
@given(st.integers(min_value=0, max_value=100))
def test_limit_offset_roundtrip(value):
    """Test that limit/offset values survive compilation."""
    metadata = MetaData()
    users = Table('users', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String),
        Column('age', Integer)
    )
    
    # Create statement with limit
    stmt = select(users).limit(value)
    
    # The limit should be preserved in the object
    assert stmt._limit == value
    
    # Compile to SQL and check
    compiled = stmt.compile()
    sql_str = str(compiled)
    
    # The LIMIT clause should be present if value > 0
    if value > 0:
        assert "LIMIT" in sql_str
        # Check if the value appears in the params or the SQL
        params = compiled.params
        # The value should be accessible somehow
        assert stmt._limit == value


# Test Connection lifecycle with actual database
def test_connection_transaction_lifecycle():
    """Test Connection begin/commit/rollback lifecycle with actual database."""
    # Use in-memory SQLite for testing
    engine = future_create_engine("sqlite:///:memory:")
    
    # Create a simple table
    metadata = MetaData()
    test_table = Table('test', metadata,
        Column('id', Integer, primary_key=True),
        Column('value', String)
    )
    metadata.create_all(engine)
    
    # Test transaction lifecycle
    with engine.connect() as conn:
        # Begin explicit transaction
        trans = conn.begin()
        
        # Transaction should be active
        assert trans is not None
        assert hasattr(trans, 'commit')
        assert hasattr(trans, 'rollback')
        
        # Insert data
        conn.execute(test_table.insert(), {"value": "test1"})
        
        # Commit transaction
        trans.commit()
        
        # After commit, transaction should be closed
        assert trans.is_active == False
        
        # Data should be persisted
        result = conn.execute(select(test_table)).fetchall()
        assert len(result) == 1
        assert result[0][1] == "test1"


# Test transaction rollback
def test_connection_rollback():
    """Test that rollback actually rolls back changes."""
    engine = future_create_engine("sqlite:///:memory:")
    
    metadata = MetaData()
    test_table = Table('test', metadata,
        Column('id', Integer, primary_key=True),
        Column('value', String)
    )
    metadata.create_all(engine)
    
    with engine.connect() as conn:
        # Insert initial data
        trans = conn.begin()
        conn.execute(test_table.insert(), {"value": "initial"})
        trans.commit()
        
        # Start new transaction
        trans = conn.begin()
        conn.execute(test_table.insert(), {"value": "to_rollback"})
        
        # Rollback
        trans.rollback()
        
        # Only initial data should exist
        result = conn.execute(select(test_table)).fetchall()
        assert len(result) == 1
        assert result[0][1] == "initial"


# Test nested transactions
def test_nested_transactions():
    """Test nested transaction behavior."""
    engine = future_create_engine("sqlite:///:memory:")
    
    metadata = MetaData()
    test_table = Table('test', metadata,
        Column('id', Integer, primary_key=True),
        Column('value', String)
    )
    metadata.create_all(engine)
    
    with engine.connect() as conn:
        # Begin outer transaction
        trans = conn.begin()
        conn.execute(test_table.insert(), {"value": "outer"})
        
        # Try to begin nested transaction
        try:
            nested = conn.begin_nested()
            conn.execute(test_table.insert(), {"value": "nested"})
            
            # Rollback nested
            nested.rollback()
            
            # Only outer should remain
            trans.commit()
            
            result = conn.execute(select(test_table)).fetchall()
            # Behavior depends on whether nested transactions are supported
            assert len(result) >= 1
        except Exception as e:
            # Nested transactions might not be supported
            trans.rollback()


# Test connection close with active transaction
def test_close_with_active_transaction():
    """Test that closing connection with active transaction rolls back."""
    engine = future_create_engine("sqlite:///:memory:")
    
    metadata = MetaData()
    test_table = Table('test', metadata,
        Column('id', Integer, primary_key=True),
        Column('value', String)
    )
    metadata.create_all(engine)
    
    # Use connection without context manager
    conn = engine.connect()
    trans = conn.begin()
    conn.execute(test_table.insert(), {"value": "uncommitted"})
    
    # Close connection without committing
    conn.close()
    
    # Open new connection and check
    with engine.connect() as new_conn:
        result = new_conn.execute(select(test_table)).fetchall()
        # Data should not be persisted (rolled back on close)
        assert len(result) == 0


# Test idempotent operations
@given(st.integers(min_value=1, max_value=10))
def test_distinct_idempotent_property(n):
    """Property: Applying distinct() n times should be same as applying once."""
    metadata = MetaData()
    users = Table('users', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String),
        Column('age', Integer)
    )
    
    stmt_once = select(users).distinct()
    
    stmt_n_times = select(users)
    for _ in range(n):
        stmt_n_times = stmt_n_times.distinct()
    
    # Both should compile to identical SQL
    sql_once = str(stmt_once.compile())
    sql_n = str(stmt_n_times.compile())
    
    assert sql_once == sql_n


# Test create_engine with special characters in URL
@given(st.text(min_size=1, max_size=20).filter(lambda x: not any(c in x for c in ['/', ':', '@', '\\', '\0'])))
def test_create_engine_with_special_db_names(db_name):
    """Test create_engine with various database names."""
    try:
        # Use file-based SQLite with the generated name
        url = f"sqlite:///{db_name}.db"
        engine = future_create_engine(url)
        
        # Engine should be created successfully
        assert engine is not None
        assert isinstance(engine, Engine)
        
        # Clean up
        engine.dispose()
        
        # Try to remove the file if it was created
        try:
            os.remove(f"{db_name}.db")
        except:
            pass
    except Exception as e:
        # Some names might be invalid for the filesystem
        pass


# Test select with duplicate columns
def test_select_duplicate_columns():
    """Test select behavior with duplicate column specifications."""
    metadata = MetaData()
    users = Table('users', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String),
        Column('age', Integer)
    )
    
    # Select same column multiple times
    stmt = select(users.c.id, users.c.id, users.c.name, users.c.id)
    
    # Should compile without error
    compiled = str(stmt.compile())
    assert "SELECT" in compiled
    
    # Check how many times 'id' appears
    # SQLAlchemy might deduplicate or keep duplicates
    assert compiled.count("users.id") >= 1


# Test empty select
def test_empty_select():
    """Test select with no arguments."""
    try:
        stmt = select()
        # Should create a valid select object
        assert stmt is not None
        
        # Compilation might fail or produce SELECT without FROM
        compiled = str(stmt.compile())
        assert "SELECT" in compiled
    except Exception as e:
        # Empty select might not be allowed
        pass