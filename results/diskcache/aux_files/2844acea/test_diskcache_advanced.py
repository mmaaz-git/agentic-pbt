"""Advanced property-based tests for diskcache to find edge cases."""

import json
import math
import tempfile
import shutil
import time
from hypothesis import assume, given, settings, strategies as st, note
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, Bundle, invariant

import diskcache
from diskcache import Cache, JSONDisk, Deque, Index


# Test with very large keys and values
@given(
    st.text(min_size=1000, max_size=10000),
    st.binary(min_size=1000, max_size=10000)
)
@settings(max_examples=10)
def test_cache_large_keys_values(key, value):
    """Test cache with very large keys and values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = Cache(tmpdir)
        
        # Set the value
        result = cache.set(key, value)
        assert result is True
        
        # Get should return the same value
        retrieved = cache.get(key)
        assert retrieved == value


# Test JSONDisk with edge case JSON values
@given(
    st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-1e308, max_value=1e308),
            st.floats(allow_nan=False, allow_infinity=False, min_value=-1e308, max_value=1e308),
            st.text(alphabet=st.characters(blacklist_categories=['Cc', 'Cs'])),
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=10),
            st.dictionaries(
                st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_categories=['Cc', 'Cs'])),
                children,
                max_size=10
            )
        ),
        max_leaves=100
    )
)
def test_jsondisk_complex_nested_structures(value):
    """Test JSONDisk with deeply nested structures."""
    with tempfile.TemporaryDirectory() as tmpdir:
        disk = JSONDisk(tmpdir)
        
        try:
            # Store and fetch
            size, mode, filename, db_value = disk.store(value, read=False)
            result = disk.fetch(mode, filename, db_value, read=False)
            assert result == value
        except (RecursionError, OverflowError, ValueError) as e:
            # These are expected for very deep nesting or extreme values
            note(f"Expected error for extreme input: {e}")
            assume(False)


# Test cache expiration
@given(
    st.text(min_size=1, max_size=20),
    st.integers(),
    st.floats(min_value=0.001, max_value=0.1)  # Short expiration times
)
def test_cache_expiration_property(key, value, expire_time):
    """Test that expired items are not retrievable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = Cache(tmpdir)
        
        # Set with expiration
        cache.set(key, value, expire=expire_time)
        
        # Immediately after setting, should be retrievable
        assert cache.get(key) == value
        
        # Wait for expiration
        time.sleep(expire_time + 0.01)
        
        # Should no longer be retrievable
        assert cache.get(key) is None
        assert key not in cache


# Test special characters in keys
@given(
    st.text(alphabet=st.characters(min_codepoint=0, max_codepoint=0x10ffff), min_size=1),
    st.integers()
)
def test_cache_unicode_keys(key, value):
    """Test cache with various Unicode characters in keys."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = Cache(tmpdir)
        
        # Skip if key contains null bytes (SQLite limitation)
        assume('\x00' not in key)
        
        # Set and get
        cache.set(key, value)
        assert cache.get(key) == value


# Test Index (persistent dictionary) properties
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.integers(),
        min_size=1,
        max_size=10
    )
)
def test_index_dictionary_semantics(items):
    """Test that Index maintains dictionary semantics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        index = Index(tmpdir)
        
        # Add all items
        for key, value in items.items():
            index[key] = value
        
        # Check all operations
        assert len(index) == len(items)
        assert set(index.keys()) == set(items.keys())
        assert set(index.values()) == set(items.values())
        
        # Test iteration
        for key in index:
            assert key in items
            assert index[key] == items[key]
        
        # Test pop
        if items:
            key = next(iter(items))
            value = index.pop(key)
            assert value == items[key]
            assert key not in index


# Stateful testing for Cache
class CacheStateMachine(RuleBasedStateMachine):
    """Stateful testing for Cache to find ordering/consistency bugs."""
    
    def __init__(self):
        super().__init__()
        self.tmpdir = tempfile.mkdtemp()
        self.cache = Cache(self.tmpdir)
        self.model = {}  # Our model of what should be in the cache
    
    keys = Bundle('keys')
    
    @initialize()
    def setup(self):
        """Initialize the state machine."""
        pass
    
    @rule(
        target=keys,
        key=st.text(min_size=1, max_size=20),
        value=st.integers()
    )
    def set_item(self, key, value):
        """Set an item in the cache."""
        result = self.cache.set(key, value)
        assert result is True
        self.model[key] = value
        return key
    
    @rule(key=keys)
    def get_item(self, key):
        """Get an item from the cache."""
        expected = self.model.get(key)
        actual = self.cache.get(key)
        assert actual == expected, f"Expected {expected}, got {actual} for key {key}"
    
    @rule(key=keys)
    def delete_item(self, key):
        """Delete an item from the cache."""
        if key in self.model:
            result = self.cache.delete(key)
            assert result is True
            del self.model[key]
            assert key not in self.cache
    
    @rule(key=keys, delta=st.integers(min_value=-100, max_value=100))
    def increment_item(self, key, delta):
        """Increment a numeric item."""
        if key in self.model and isinstance(self.model[key], int):
            new_value = self.cache.incr(key, delta)
            self.model[key] += delta
            assert new_value == self.model[key]
    
    @invariant()
    def check_length(self):
        """Check that cache length matches model."""
        assert len(self.cache) == len(self.model)
    
    @invariant()
    def check_contains(self):
        """Check that all model keys are in cache and vice versa."""
        for key in self.model:
            assert key in self.cache
        # Note: Can't easily check the reverse without iterating cache
    
    def teardown(self):
        """Clean up after test."""
        self.cache.close()
        shutil.rmtree(self.tmpdir)


# Test cache pop with default values
@given(
    st.text(min_size=1, max_size=20),
    st.integers(),
    st.integers()
)
def test_cache_pop_with_default(key, value, default):
    """Test cache.pop() with default values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = Cache(tmpdir)
        
        # Pop non-existent key should return default
        result = cache.pop(key, default=default)
        assert result == default
        
        # Set and pop should return value
        cache.set(key, value)
        result = cache.pop(key)
        assert result == value
        
        # Key should be gone
        assert key not in cache


# Test Deque with mixed operations
@given(
    st.lists(
        st.tuples(
            st.sampled_from(['append', 'appendleft', 'pop', 'popleft']),
            st.integers()
        ),
        min_size=1,
        max_size=20
    )
)
def test_deque_mixed_operations(operations):
    """Test Deque with mixed append/pop operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        deque = Deque(directory=tmpdir)
        model = []  # Track what should be in deque
        
        for op, value in operations:
            if op == 'append':
                deque.append(value)
                model.append(value)
            elif op == 'appendleft':
                deque.appendleft(value)
                model.insert(0, value)
            elif op == 'pop' and len(deque) > 0:
                actual = deque.pop()
                expected = model.pop()
                assert actual == expected
            elif op == 'popleft' and len(deque) > 0:
                actual = deque.popleft()
                expected = model.pop(0)
                assert actual == expected
        
        # Final state should match
        assert list(deque) == model


# Test cache clear operation
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.integers(),
        min_size=1,
        max_size=10
    )
)
def test_cache_clear_operation(items):
    """Test that cache.clear() removes all items."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = Cache(tmpdir)
        
        # Add items
        for key, value in items.items():
            cache.set(key, value)
        
        assert len(cache) == len(items)
        
        # Clear cache
        cache.clear()
        
        # Should be empty
        assert len(cache) == 0
        for key in items:
            assert key not in cache


# Test cache with bytes keys and values
@given(
    st.binary(min_size=1, max_size=100),
    st.binary(min_size=1, max_size=1000)
)
def test_cache_binary_keys_values(key, value):
    """Test cache with binary keys and values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = Cache(tmpdir)
        
        # Avoid null bytes in keys
        assume(b'\x00' not in key)
        
        cache.set(key, value)
        assert cache.get(key) == value


# Run the stateful test
TestCacheStateMachine = CacheStateMachine.TestCase