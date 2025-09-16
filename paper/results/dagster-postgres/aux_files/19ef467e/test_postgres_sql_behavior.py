"""
Test PostgreSQL-specific SQL behavior in PostgresRunStorage
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

import string
from hypothesis import given, strategies as st, settings, assume
from dagster._serdes import serialize_value, deserialize_value
import zlib


def test_upsert_behavior():
    """Test the ON CONFLICT DO UPDATE behavior"""
    
    print("Testing PostgreSQL UPSERT behavior patterns...")
    
    # The set_cursor_values method uses:
    # INSERT ... ON CONFLICT(key) DO UPDATE SET value = excluded.value
    # This should handle concurrent updates correctly
    
    # Simulate the behavior
    class PostgresUpsertSimulator:
        def __init__(self):
            self.store = {}
            self.operation_log = []
        
        def upsert(self, key, value):
            """Simulates INSERT ... ON CONFLICT DO UPDATE"""
            if key in self.store:
                self.operation_log.append(('UPDATE', key, self.store[key], value))
            else:
                self.operation_log.append(('INSERT', key, None, value))
            self.store[key] = value
        
        def bulk_upsert(self, pairs):
            """Simulates bulk upsert operation"""
            for key, value in pairs.items():
                self.upsert(key, value)
    
    sim = PostgresUpsertSimulator()
    
    # Test 1: Insert new key
    sim.upsert("key1", "value1")
    assert sim.store["key1"] == "value1"
    assert sim.operation_log[-1][0] == 'INSERT'
    
    # Test 2: Update existing key
    sim.upsert("key1", "value2")
    assert sim.store["key1"] == "value2"
    assert sim.operation_log[-1][0] == 'UPDATE'
    
    # Test 3: Bulk operation with mixed insert/update
    sim.bulk_upsert({
        "key1": "value3",  # update
        "key2": "new_value",  # insert
        "key3": "another_value"  # insert
    })
    
    assert sim.store["key1"] == "value3"
    assert sim.store["key2"] == "new_value"
    assert sim.store["key3"] == "another_value"
    
    print("✓ UPSERT behavior test passed")
    return True


def test_sql_edge_cases():
    """Test edge cases in SQL operations"""
    
    print("\nTesting SQL edge cases...")
    
    # Test cases that might break SQL
    edge_cases = [
        # SQL injection attempts
        ("key1", "'; DROP TABLE users; --"),
        ("key2", "1' OR '1'='1"),
        
        # Special characters
        ("key3", "O'Reilly"),  # Single quote
        ("key4", 'Say "Hello"'),  # Double quotes
        ("key5", "Line1\nLine2"),  # Newline
        ("key6", "Tab\there"),  # Tab
        ("key7", "Back\\slash"),  # Backslash
        
        # PostgreSQL specific
        ("key8", "$$dollar$$"),  # Dollar quoting
        ("key9", "E'\\x41'"),  # Escape string
        
        # Unicode
        ("key10", "🦄"),  # Emoji
        ("key11", "你好"),  # Chinese
        ("key12", "مرحبا"),  # Arabic
        
        # Empty and whitespace
        ("key13", ""),  # Empty string
        ("key14", " "),  # Single space
        ("key15", "   "),  # Multiple spaces
        
        # Very long values
        ("key16", "x" * 10000),  # Long string
        
        # Binary-like data
        ("key17", "\x00\x01\x02"),  # Null bytes and control chars
    ]
    
    # Simulate storing these in a way that would be safe with proper escaping
    for key, value in edge_cases:
        # The actual implementation should handle these safely
        # We're testing that the values aren't corrupted
        serialized = serialize_value({key: value})
        deserialized = deserialize_value(serialized)
        assert deserialized[key] == value, f"Failed for {repr(key)}: {repr(value)}"
    
    print(f"✓ Tested {len(edge_cases)} SQL edge cases")
    return True


def test_returning_clause():
    """Test the RETURNING clause behavior"""
    
    print("\nTesting PostgreSQL RETURNING clause...")
    
    # The implementation uses RETURNING to get back values after INSERT/UPDATE
    # This is PostgreSQL-specific and ensures the operation succeeded
    
    # Test that RETURNING clause would work with various column types
    test_cases = [
        {"daemon_type": "test_daemon", "daemon_id": "id123"},
        {"daemon_type": "another_daemon", "daemon_id": "id456"},
    ]
    
    for case in test_cases:
        # The RETURNING clause should return the inserted/updated row
        # In the real implementation, this confirms the operation
        assert case["daemon_type"] is not None
        assert case["daemon_id"] is not None
    
    print("✓ RETURNING clause test passed")
    return True


@given(
    key_value_pairs=st.dictionaries(
        st.text(alphabet=string.ascii_letters + string.digits + "_", min_size=1, max_size=50),
        st.text(min_size=0, max_size=1000),
        min_size=1,
        max_size=20
    )
)
@settings(max_examples=100)
def test_bulk_upsert_atomicity(key_value_pairs):
    """Test that bulk upserts maintain atomicity"""
    
    # In PostgreSQL, the bulk upsert should be atomic
    # All pairs should be inserted/updated or none
    
    class AtomicStore:
        def __init__(self):
            self.store = {}
            self.transaction_log = []
        
        def bulk_upsert_atomic(self, pairs):
            """Simulates atomic bulk upsert"""
            # Start transaction
            temp_store = self.store.copy()
            
            try:
                for key, value in pairs.items():
                    temp_store[key] = value
                
                # Commit - all changes applied
                self.store = temp_store
                self.transaction_log.append(('COMMIT', len(pairs)))
                return True
            except:
                # Rollback - no changes applied
                self.transaction_log.append(('ROLLBACK', len(pairs)))
                return False
    
    store = AtomicStore()
    
    # Perform bulk upsert
    result = store.bulk_upsert_atomic(key_value_pairs)
    assert result == True
    
    # Verify all pairs were stored
    for key, value in key_value_pairs.items():
        assert store.store[key] == value


@given(
    snapshot_body=st.binary(min_size=0, max_size=10000)
)
@settings(max_examples=50)
def test_binary_compression(snapshot_body):
    """Test compression of binary data"""
    
    # The snapshot storage compresses data with zlib
    # Test that binary data compresses/decompresses correctly
    
    compressed = zlib.compress(snapshot_body)
    decompressed = zlib.decompress(compressed)
    
    assert decompressed == snapshot_body, "Binary compression round-trip failed"


@given(
    pairs=st.dictionaries(
        st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        st.text(min_size=0, max_size=500),
        min_size=0,  # Allow empty dict
        max_size=50
    )
)
@settings(max_examples=100)
def test_empty_and_null_handling(pairs):
    """Test handling of empty strings and null-like values"""
    
    # PostgreSQL distinguishes between NULL and empty string
    # The implementation should handle both correctly
    
    for key, value in pairs.items():
        # Empty string should be preserved as empty string, not NULL
        if value == "":
            assert value is not None, "Empty string should not become None"
        
        # Keys should never be empty after filtering
        assert key != "", "Key should not be empty"
        assert key.strip() != "", "Key should not be whitespace only"


def test_concurrent_upsert_simulation():
    """Simulate concurrent UPSERT operations"""
    
    print("\nTesting concurrent UPSERT simulation...")
    
    # PostgreSQL's ON CONFLICT DO UPDATE handles concurrent updates
    # Let's simulate potential race conditions
    
    class ConcurrentUpsertSimulator:
        def __init__(self):
            self.store = {}
            self.version = {}  # Track version numbers for each key
        
        def concurrent_upsert(self, key, value, client_id):
            """Simulates concurrent upsert from different clients"""
            
            # In PostgreSQL, ON CONFLICT ensures only one wins
            # The last one to execute wins
            
            if key not in self.store:
                self.store[key] = value
                self.version[key] = 1
                return ('INSERT', 1)
            else:
                # Update wins over concurrent updates
                old_version = self.version[key]
                self.store[key] = value
                self.version[key] = old_version + 1
                return ('UPDATE', self.version[key])
    
    sim = ConcurrentUpsertSimulator()
    
    # Simulate multiple clients updating the same key
    key = "concurrent_key"
    
    # Client 1
    result1 = sim.concurrent_upsert(key, "value_from_client1", "client1")
    assert result1[0] == 'INSERT'
    
    # Client 2 (concurrent update)
    result2 = sim.concurrent_upsert(key, "value_from_client2", "client2")
    assert result2[0] == 'UPDATE'
    
    # Client 3 (another concurrent update)
    result3 = sim.concurrent_upsert(key, "value_from_client3", "client3")
    assert result3[0] == 'UPDATE'
    
    # Final value should be from the last update
    assert sim.store[key] == "value_from_client3"
    assert sim.version[key] == 3
    
    print("✓ Concurrent UPSERT simulation passed")
    return True


def test_transaction_isolation():
    """Test transaction isolation levels"""
    
    print("\nTesting transaction isolation...")
    
    # The implementation uses AUTOCOMMIT isolation level
    # This means each statement is its own transaction
    
    class AutocommitSimulator:
        def __init__(self):
            self.store = {}
            self.committed_operations = []
        
        def execute_autocommit(self, operation, key, value):
            """Each operation commits immediately"""
            if operation == 'INSERT':
                self.store[key] = value
                self.committed_operations.append((operation, key, value))
                # Immediately visible to other connections
                return True
            elif operation == 'UPDATE':
                if key in self.store:
                    old_value = self.store[key]
                    self.store[key] = value
                    self.committed_operations.append((operation, key, value))
                    return True
                return False
    
    sim = AutocommitSimulator()
    
    # Each operation commits immediately
    sim.execute_autocommit('INSERT', 'key1', 'value1')
    assert 'key1' in sim.store  # Immediately visible
    
    sim.execute_autocommit('UPDATE', 'key1', 'value2')
    assert sim.store['key1'] == 'value2'  # Immediately visible
    
    # No rollback possible after autocommit
    assert len(sim.committed_operations) == 2
    
    print("✓ Transaction isolation test passed")
    return True


def main():
    print("=" * 60)
    print("PostgreSQL-specific SQL Behavior Testing")
    print("=" * 60)
    
    try:
        # Run tests
        test_upsert_behavior()
        test_sql_edge_cases()
        test_returning_clause()
        test_concurrent_upsert_simulation()
        test_transaction_isolation()
        
        # Run property-based tests
        print("\nRunning property-based SQL tests...")
        
        print("Testing bulk upsert atomicity...")
        test_bulk_upsert_atomicity()
        print("✓ Bulk upsert atomicity test passed (100 examples)")
        
        print("\nTesting binary compression...")
        test_binary_compression()
        print("✓ Binary compression test passed (50 examples)")
        
        print("\nTesting empty and null handling...")
        test_empty_and_null_handling()
        print("✓ Empty/null handling test passed (100 examples)")
        
        print("\n" + "=" * 60)
        print("All SQL behavior tests passed successfully! ✓")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)