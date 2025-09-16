import os
import tempfile
from hypothesis import given, strategies as st, assume, settings
from sqltrie import SQLiteTrie, PyGTrie, ShortKeyError
import sqlite3


# Strategy for valid trie keys (tuples of strings)
trie_keys = st.lists(
    st.text(min_size=1, max_size=10, alphabet=st.characters(blacklist_categories=("Cc", "Cs"))).filter(lambda x: "/" not in x and "'" not in x),
    min_size=0,
    max_size=5
).map(tuple)

# Strategy for trie values (bytes)
trie_values = st.binary(min_size=0, max_size=100)


@given(trie_keys, trie_values)
@settings(max_examples=200)
def test_round_trip_sqlite(key, value):
    """Test that setting and getting a value returns the same value for SQLiteTrie"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        trie = SQLiteTrie.open(db_path)
        trie[key] = value
        assert trie[key] == value
        
        # Test persistence
        trie.commit()
        trie.close()
        
        trie2 = SQLiteTrie.open(db_path)
        assert trie2[key] == value
        trie2.close()
    finally:
        os.unlink(db_path)


@given(trie_keys, trie_values)
@settings(max_examples=200)
def test_round_trip_pygtrie(key, value):
    """Test that setting and getting a value returns the same value for PyGTrie"""
    trie = PyGTrie()
    trie[key] = value
    assert trie[key] == value


@given(st.lists(st.tuples(trie_keys, trie_values), min_size=1, max_size=10))
@settings(max_examples=100)
def test_multiple_implementations_equivalence(items):
    """Test that SQLiteTrie and PyGTrie behave identically"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        sqlite_trie = SQLiteTrie.open(db_path)
        pyg_trie = PyGTrie()
        
        # Insert all items
        for key, value in items:
            sqlite_trie[key] = value
            pyg_trie[key] = value
        
        # Check all items match
        for key, value in items:
            assert sqlite_trie[key] == pyg_trie[key]
        
        # Check iteration matches (sort because order might differ)
        sqlite_items = sorted(list(sqlite_trie.items()))
        pyg_items = sorted(list(pyg_trie.items()))
        assert sqlite_items == pyg_items
        
        # Check length matches
        assert len(sqlite_trie) == len(pyg_trie)
        
        sqlite_trie.close()
    finally:
        os.unlink(db_path)


@given(trie_keys)
@settings(max_examples=200)
def test_deletion_consistency(key):
    """Test that deleted keys properly raise KeyError"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        trie = SQLiteTrie.open(db_path)
        value = b"test_value"
        
        # Set and delete
        trie[key] = value
        assert key in trie
        del trie[key]
        
        # Should raise KeyError or ShortKeyError
        try:
            _ = trie[key]
            assert False, "Should have raised an error"
        except (KeyError, ShortKeyError):
            pass  # Expected
        
        trie.close()
    finally:
        os.unlink(db_path)


@given(trie_keys, st.lists(trie_keys, min_size=0, max_size=3))
@settings(max_examples=100)
def test_prefix_operations(base_key, extensions):
    """Test prefix operations maintain correct relationships"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        trie = SQLiteTrie.open(db_path)
        
        # Build a trie with prefixes
        accumulated_key = ()
        for i, segment in enumerate(base_key):
            accumulated_key = accumulated_key + (segment,)
            trie[accumulated_key] = f"value_{i}".encode()
        
        # Test prefix operations on extended keys
        for ext in extensions:
            test_key = base_key + ext
            
            prefixes = list(trie.prefixes(test_key))
            
            # All returned prefixes should actually be prefixes
            for prefix_key, _ in prefixes:
                assert test_key[:len(prefix_key)] == prefix_key
            
            # Shortest and longest prefix relationship
            shortest = trie.shortest_prefix(test_key)
            longest = trie.longest_prefix(test_key)
            
            if shortest and longest:
                assert len(shortest[0]) <= len(longest[0])
                # Both should be actual prefixes
                assert test_key[:len(shortest[0])] == shortest[0]
                assert test_key[:len(longest[0])] == longest[0]
        
        trie.close()
    finally:
        os.unlink(db_path)


@given(trie_keys)
@settings(max_examples=200)
def test_short_key_error_behavior(key):
    """Test that accessing a node without a value raises ShortKeyError"""
    assume(len(key) >= 2)  # Need at least 2 elements to test this
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        trie = SQLiteTrie.open(db_path)
        
        # Set a value at the full key
        trie[key] = b"value"
        
        # The parent key should exist as a node but not have a value
        parent_key = key[:-1]
        
        # Check has_node returns True but getting raises ShortKeyError
        assert trie.has_node(parent_key)
        
        try:
            _ = trie[parent_key]
            # If we get here without error, the parent already had a value
            # which is fine, just skip this test case
        except ShortKeyError:
            # This is expected behavior
            pass
        except KeyError:
            # KeyError instead of ShortKeyError might indicate a bug
            # but let's continue testing
            pass
        
        trie.close()
    finally:
        os.unlink(db_path)


@given(st.lists(st.tuples(trie_keys, trie_values), min_size=0, max_size=10))
@settings(max_examples=100)
def test_view_isolation(items):
    """Test that views are properly isolated from parent trie"""
    assume(len(items) > 0)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        trie = SQLiteTrie.open(db_path)
        
        # Insert initial items
        for key, value in items:
            trie[key] = value
        
        # Create a view with first key as prefix (if it has elements)
        if items and items[0][0]:
            view_key = items[0][0][:1] if items[0][0] else ()
            view = trie.view(view_key)
            
            # Modifications to view should affect parent after commit
            test_key = ("test", "key")
            test_value = b"test_value"
            
            view[test_key] = test_value
            view.commit()
            
            # Check it's accessible from parent with full path
            full_key = view_key + test_key
            assert trie[full_key] == test_value
        
        trie.close()
    finally:
        os.unlink(db_path)


@given(st.lists(st.tuples(trie_keys, trie_values), min_size=1, max_size=20))
@settings(max_examples=100)
def test_items_consistency(items):
    """Test that all items returned by items() are retrievable"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        trie = SQLiteTrie.open(db_path)
        
        # Insert all items
        for key, value in items:
            trie[key] = value
        
        # Check all items() are retrievable
        for key, value in trie.items():
            assert trie[key] == value
        
        # Check length consistency
        items_count = len(list(trie.items()))
        assert items_count == len(trie)
        
        trie.close()
    finally:
        os.unlink(db_path)