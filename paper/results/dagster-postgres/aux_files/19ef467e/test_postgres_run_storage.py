"""
Property-based tests for PostgresRunStorage using Hypothesis
"""

import os
import tempfile
import string
from hypothesis import given, strategies as st, settings, assume
from dagster_postgres.run_storage import PostgresRunStorage
import sqlalchemy as db


# Test configuration
SQLITE_TEST_URL = "sqlite:///test_run_storage.db"


def create_test_storage():
    """Create a test storage instance using SQLite for simplicity"""
    # Since PostgresRunStorage requires postgres, we'll test the core logic
    # by creating a minimal test database
    return PostgresRunStorage(
        postgres_url=SQLITE_TEST_URL,
        should_autocreate_tables=True
    )


def cleanup_test_storage():
    """Clean up test database file"""
    if os.path.exists("test_run_storage.db"):
        os.remove("test_run_storage.db")


# Strategy for valid cursor keys and values (non-empty strings)
cursor_key_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "_-",
    min_size=1,
    max_size=50
)
cursor_value_strategy = st.text(min_size=1, max_size=500)


# Test 1: Round-trip property for cursor values
@given(
    pairs=st.dictionaries(
        cursor_key_strategy,
        cursor_value_strategy,
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100)
def test_cursor_values_round_trip(pairs):
    """
    Property: set_cursor_values followed by get_cursor_values should return the same values
    """
    cleanup_test_storage()
    try:
        storage = create_test_storage()
        
        # Set cursor values
        storage.set_cursor_values(pairs)
        
        # Get cursor values back
        keys_set = set(pairs.keys())
        retrieved = storage.get_cursor_values(keys_set)
        
        # Check round-trip property
        assert retrieved == pairs, f"Round-trip failed: set {pairs}, got {retrieved}"
        
    finally:
        cleanup_test_storage()


# Test 2: Update property for cursor values
@given(
    key=cursor_key_strategy,
    initial_value=cursor_value_strategy,
    updated_value=cursor_value_strategy
)
@settings(max_examples=100)
def test_cursor_values_update(key, initial_value, updated_value):
    """
    Property: Setting a cursor value multiple times should result in the last value being stored
    """
    cleanup_test_storage()
    try:
        storage = create_test_storage()
        
        # Set initial value
        storage.set_cursor_values({key: initial_value})
        
        # Update with new value
        storage.set_cursor_values({key: updated_value})
        
        # Get value back
        retrieved = storage.get_cursor_values({key})
        
        # Check that the last value is stored
        assert retrieved[key] == updated_value, f"Update failed: expected {updated_value}, got {retrieved[key]}"
        
    finally:
        cleanup_test_storage()


# Test 3: Index migration cache consistency
@given(
    migration_name=st.text(
        alphabet=string.ascii_letters + string.digits + "_",
        min_size=1,
        max_size=50
    )
)
@settings(max_examples=100)
def test_index_migration_cache_consistency(migration_name):
    """
    Property: After mark_index_built is called, has_built_index should always return True
    """
    cleanup_test_storage()
    try:
        storage = create_test_storage()
        
        # Initially may be False (or True if already exists)
        initial_state = storage.has_built_index(migration_name)
        
        # Mark index as built
        storage.mark_index_built(migration_name)
        
        # Now it should always return True
        assert storage.has_built_index(migration_name) == True, \
            f"After marking index built, has_built_index should return True"
        
        # Check multiple times to ensure consistency
        for _ in range(5):
            assert storage.has_built_index(migration_name) == True, \
                "has_built_index should consistently return True after marking built"
        
    finally:
        cleanup_test_storage()


# Test 4: Multiple cursor values set atomically
@given(
    pairs1=st.dictionaries(cursor_key_strategy, cursor_value_strategy, min_size=1, max_size=5),
    pairs2=st.dictionaries(cursor_key_strategy, cursor_value_strategy, min_size=1, max_size=5)
)
@settings(max_examples=100)
def test_cursor_values_merge(pairs1, pairs2):
    """
    Property: Setting cursor values should merge with existing values (upsert behavior)
    """
    cleanup_test_storage()
    try:
        storage = create_test_storage()
        
        # Set first batch
        storage.set_cursor_values(pairs1)
        
        # Set second batch (may have overlapping keys)
        storage.set_cursor_values(pairs2)
        
        # Get all keys
        all_keys = set(pairs1.keys()) | set(pairs2.keys())
        retrieved = storage.get_cursor_values(all_keys)
        
        # Check that all keys are present with correct values
        expected = {**pairs1, **pairs2}  # pairs2 overwrites pairs1 for common keys
        assert retrieved == expected, f"Merge failed: expected {expected}, got {retrieved}"
        
    finally:
        cleanup_test_storage()


# Test 5: Empty operations
@given(
    key=cursor_key_strategy
)
@settings(max_examples=50)
def test_get_nonexistent_cursor_value(key):
    """
    Property: Getting non-existent cursor values should return empty dict
    """
    cleanup_test_storage()
    try:
        storage = create_test_storage()
        
        # Get non-existent key
        retrieved = storage.get_cursor_values({key})
        
        # Should return empty dict for non-existent keys
        assert retrieved == {}, f"Expected empty dict for non-existent key, got {retrieved}"
        
    finally:
        cleanup_test_storage()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])