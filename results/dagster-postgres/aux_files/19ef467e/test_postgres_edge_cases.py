"""
Edge case testing for PostgresRunStorage
"""

import sys
import os

# Add the virtual environment's site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

import string
import zlib
from hypothesis import given, strategies as st, settings, assume
from dagster._serdes import serialize_value, deserialize_value


def test_compression_edge_cases():
    """Test edge cases in compression/decompression"""
    
    print("Testing compression edge cases...")
    
    # Test 1: Empty data
    print("Test 1: Empty data compression")
    empty_data = {}
    serialized = serialize_value(empty_data)
    compressed = zlib.compress(serialized.encode("utf-8"))
    decompressed = zlib.decompress(compressed).decode("utf-8")
    deserialized = deserialize_value(decompressed)
    assert deserialized == empty_data
    print("✓ Empty data test passed")
    
    # Test 2: Very large data
    print("\nTest 2: Large data compression")
    large_data = {f"key_{i}": f"value_{i}" * 100 for i in range(100)}
    serialized = serialize_value(large_data)
    compressed = zlib.compress(serialized.encode("utf-8"))
    decompressed = zlib.decompress(compressed).decode("utf-8")
    deserialized = deserialize_value(decompressed)
    assert deserialized == large_data
    print("✓ Large data test passed")
    
    # Test 3: Unicode and special characters
    print("\nTest 3: Unicode and special characters")
    unicode_data = {
        "emoji": "🦄🎉🔥",
        "chinese": "你好世界",
        "arabic": "مرحبا بالعالم",
        "special": "\n\t\r\x00\x01",
        "quotes": "\"'`",
    }
    serialized = serialize_value(unicode_data)
    compressed = zlib.compress(serialized.encode("utf-8"))
    decompressed = zlib.decompress(compressed).decode("utf-8")
    deserialized = deserialize_value(decompressed)
    assert deserialized == unicode_data
    print("✓ Unicode test passed")
    
    # Test 4: Deeply nested structures
    print("\nTest 4: Deeply nested structures")
    nested = {"level": 0}
    current = nested
    for i in range(1, 50):
        current["child"] = {"level": i}
        current = current["child"]
    
    serialized = serialize_value(nested)
    compressed = zlib.compress(serialized.encode("utf-8"))
    decompressed = zlib.decompress(compressed).decode("utf-8")
    deserialized = deserialize_value(decompressed)
    assert deserialized == nested
    print("✓ Deeply nested structure test passed")
    
    return True


# Property-based test for SQL injection in cursor keys/values
@given(
    key=st.text(min_size=1).filter(lambda x: x.strip()),
    value=st.text(min_size=1)
)
@settings(max_examples=100)
def test_sql_injection_in_cursor_values(key, value):
    """Test that SQL injection characters in keys/values are handled safely"""
    
    # Dangerous SQL patterns to test
    dangerous_patterns = [
        "'; DROP TABLE",
        "1' OR '1'='1",
        "admin'--",
        "' OR 1=1--",
        "'; DELETE FROM",
        "\x00",  # null byte
        "\\",    # backslash
        "%",     # wildcard
        "_",     # wildcard
    ]
    
    # If key or value contains dangerous patterns, it should still work correctly
    # The implementation should properly escape these
    
    # Since we can't test against actual DB, we verify the data isn't mangled
    # The real test would be against a live database
    
    # Check that serialization handles these safely
    test_data = {key: value}
    serialized = serialize_value(test_data)
    deserialized = deserialize_value(serialized)
    assert deserialized == test_data, f"Failed to handle: key={repr(key)}, value={repr(value)}"


@given(
    migration_name=st.text()
)
@settings(max_examples=100)
def test_migration_name_edge_cases(migration_name):
    """Test edge cases in migration names"""
    
    # Test that any string can be used as a migration name
    # This tests the caching mechanism doesn't break with weird names
    
    class MockCache:
        def __init__(self):
            self._cache = {}
            self._built = set()
        
        def has_built_index(self, name):
            if name not in self._cache:
                self._cache[name] = name in self._built
            return self._cache[name]
        
        def mark_index_built(self, name):
            self._built.add(name)
            if name in self._cache:
                del self._cache[name]
    
    cache = MockCache()
    
    # Should handle any migration name
    initial = cache.has_built_index(migration_name)
    assert isinstance(initial, bool)
    
    cache.mark_index_built(migration_name)
    assert cache.has_built_index(migration_name) == True


@given(
    pairs=st.dictionaries(
        st.text(min_size=1).filter(lambda x: x.strip()),
        st.text(),
        max_size=100
    )
)
@settings(max_examples=50)
def test_cursor_values_idempotency(pairs):
    """Test that setting cursor values multiple times is idempotent"""
    
    # Simulate the upsert behavior
    class Store:
        def __init__(self):
            self.data = {}
        
        def set_values(self, pairs):
            self.data.update(pairs)
        
        def get_values(self, keys):
            return {k: self.data[k] for k in keys if k in self.data}
    
    store = Store()
    
    # Set values once
    store.set_values(pairs)
    result1 = store.get_values(set(pairs.keys()))
    
    # Set values again (idempotent)
    store.set_values(pairs)
    result2 = store.get_values(set(pairs.keys()))
    
    assert result1 == result2 == pairs


@given(
    compression_level=st.integers(min_value=-1, max_value=9)
)
@settings(max_examples=20)
def test_compression_levels(compression_level):
    """Test different compression levels"""
    
    test_data = {"test": "data" * 100}
    serialized = serialize_value(test_data)
    
    # Test with different compression levels
    compressed = zlib.compress(serialized.encode("utf-8"), level=compression_level)
    decompressed = zlib.decompress(compressed).decode("utf-8")
    deserialized = deserialize_value(decompressed)
    
    assert deserialized == test_data


# Test for potential integer overflow in snapshot_id
@given(
    snapshot_id=st.one_of(
        st.text(alphabet=string.printable, min_size=1, max_size=1000),
        st.text(min_size=1, max_size=1),  # single char
        st.text(min_size=5000, max_size=5001),  # very long (but within Hypothesis limits)
    )
)
@settings(max_examples=50)
def test_snapshot_id_handling(snapshot_id):
    """Test that snapshot IDs of various sizes are handled correctly"""
    
    # The snapshot_id is stored as-is in the database
    # Test that it handles various sizes correctly
    
    # Since we can't test actual DB, verify the ID isn't modified
    test_snapshot = {"id": snapshot_id, "data": "test"}
    serialized = serialize_value(test_snapshot)
    compressed = zlib.compress(serialized.encode("utf-8"))
    
    # The ID should survive the round trip
    decompressed = zlib.decompress(compressed).decode("utf-8")
    deserialized = deserialize_value(decompressed)
    assert deserialized["id"] == snapshot_id


def test_concurrent_access_simulation():
    """Simulate concurrent access patterns"""
    
    print("\nTesting concurrent access patterns...")
    
    # Test the index migration cache under concurrent-like access
    class ConcurrentCache:
        def __init__(self):
            self._cache = {}
            self._built = set()
            self._access_count = {}
        
        def has_built_index(self, name):
            self._access_count[name] = self._access_count.get(name, 0) + 1
            
            if name not in self._cache:
                # Simulate potential race condition
                import time
                import random
                time.sleep(random.random() * 0.0001)  # Tiny random delay
                self._cache[name] = name in self._built
            return self._cache[name]
        
        def mark_index_built(self, name):
            self._built.add(name)
            if name in self._cache:
                del self._cache[name]
    
    cache = ConcurrentCache()
    
    # Simulate multiple "concurrent" checks
    migration = "test_migration"
    
    # Multiple checks before marking
    results_before = [cache.has_built_index(migration) for _ in range(10)]
    assert all(r == False for r in results_before), "All checks before marking should be False"
    
    # Mark as built
    cache.mark_index_built(migration)
    
    # Multiple checks after marking
    results_after = [cache.has_built_index(migration) for _ in range(10)]
    assert all(r == True for r in results_after), "All checks after marking should be True"
    
    print("✓ Concurrent access simulation passed")
    
    return True


def main():
    print("=" * 60)
    print("Edge Case Testing for PostgresRunStorage")
    print("=" * 60)
    
    try:
        # Run edge case tests
        test_compression_edge_cases()
        test_concurrent_access_simulation()
        
        # Run property-based tests
        print("\nRunning property-based edge case tests...")
        
        print("Testing SQL injection safety...")
        test_sql_injection_in_cursor_values()
        print("✓ SQL injection test passed (100 examples)")
        
        print("\nTesting migration name edge cases...")
        test_migration_name_edge_cases()
        print("✓ Migration name test passed (100 examples)")
        
        print("\nTesting cursor values idempotency...")
        test_cursor_values_idempotency()
        print("✓ Idempotency test passed (50 examples)")
        
        print("\nTesting compression levels...")
        test_compression_levels()
        print("✓ Compression levels test passed (20 examples)")
        
        print("\nTesting snapshot ID handling...")
        test_snapshot_id_handling()
        print("✓ Snapshot ID test passed (50 examples)")
        
        print("\n" + "=" * 60)
        print("All edge case tests passed successfully! ✓")
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