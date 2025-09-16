import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sqltrie_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from sqltrie.pygtrie import PyGTrie
from sqltrie.trie import ShortKeyError


@st.composite
def trie_keys(draw):
    """Generate valid trie keys (tuples of strings)."""
    length = draw(st.integers(min_value=0, max_value=5))
    return tuple(draw(st.text(min_size=1, max_size=10)) for _ in range(length))


@st.composite  
def trie_with_items(draw):
    """Generate a trie with some items."""
    trie = PyGTrie()
    n_items = draw(st.integers(min_value=0, max_value=10))
    items = {}
    for _ in range(n_items):
        key = draw(trie_keys())
        value = draw(st.binary(min_size=1, max_size=100))
        trie[key] = value
        items[key] = value
    return trie, items


@given(trie_keys(), st.binary(min_size=1, max_size=100))
def test_round_trip_set_get(key, value):
    """Property: Setting and getting an item should preserve the value."""
    trie = PyGTrie()
    trie[key] = value
    assert trie[key] == value


@given(trie_with_items())
def test_length_invariant(trie_items):
    """Property: Length should match the number of items."""
    trie, items = trie_items
    assert len(trie) == len(items)
    
    # Count items manually
    count = sum(1 for _ in trie.items())
    assert count == len(items)


@given(trie_keys(), st.binary(min_size=1, max_size=100))
def test_delete_inverse(key, value):
    """Property: After deleting a key, it should not exist."""
    trie = PyGTrie()
    trie[key] = value
    assert key in trie
    
    del trie[key]
    assert key not in trie
    
    # Should raise KeyError when accessing deleted key
    with pytest.raises(KeyError):
        _ = trie[key]


@given(trie_keys(), st.binary(min_size=1, max_size=100))
def test_has_node_consistency(key, value):
    """Property: has_node should be true for any key with a value."""
    trie = PyGTrie()
    trie[key] = value
    assert trie.has_node(key)
    
    # After deletion, has_node might still be true if it has children
    del trie[key]
    # But the key should not be in the trie
    assert key not in trie


@given(trie_with_items(), trie_keys())
def test_items_with_prefix(trie_items, prefix):
    """Property: items(prefix) should only return items with that prefix."""
    trie, _ = trie_items
    
    for key, value in trie.items(prefix=prefix):
        # Key should start with prefix
        assert key[:len(prefix)] == prefix


@given(trie_with_items(), trie_keys())
def test_view_correctness(trie_items, prefix):
    """Property: A view should contain exactly the items with the given prefix, with prefix removed."""
    trie, _ = trie_items
    view = trie.view(prefix)
    
    # All items in view should correspond to items in original trie with prefix
    for key, value in view.items():
        full_key = prefix + key
        # The value in view should match the value in original trie
        if full_key in trie:
            assert trie[full_key] == value


@given(trie_keys(), st.binary(min_size=1, max_size=100))
def test_prefixes_property(key, value):
    """Property: prefixes() should return all prefixes of a key that have values."""
    trie = PyGTrie()
    
    # Add values for various prefixes
    for i in range(len(key) + 1):
        prefix = key[:i]
        trie[prefix] = value
    
    # Get all prefixes
    prefixes = list(trie.prefixes(key))
    
    # Each returned prefix should exist in the trie
    for prefix_key, prefix_value in prefixes:
        if prefix_key is not None:
            assert prefix_key in trie
            assert trie[prefix_key] == prefix_value


@given(trie_with_items(), trie_keys())
def test_longest_prefix(trie_items, key):
    """Property: longest_prefix should be the longest key in trie that is a prefix of the given key."""
    trie, items = trie_items
    
    longest = trie.longest_prefix(key)
    
    if longest is not None:
        # It should be a prefix of the key
        assert key[:len(longest)] == longest
        # It should exist in the trie
        assert longest in trie
        
        # No longer prefix should exist
        for stored_key in items:
            if len(stored_key) > len(longest) and key[:len(stored_key)] == stored_key:
                assert False, f"Found longer prefix {stored_key}"


@given(trie_with_items(), trie_keys())
def test_shortest_prefix(trie_items, key):
    """Property: shortest_prefix should be the shortest key in trie that is a prefix of the given key."""
    trie, items = trie_items
    
    shortest = trie.shortest_prefix(key)
    
    if shortest is not None and shortest[0] is not None:
        shortest_key = shortest[0]
        # It should be a prefix of the key
        assert key[:len(shortest_key)] == shortest_key
        # It should exist in the trie
        assert shortest_key in trie
        
        # No shorter prefix should exist
        for stored_key in items:
            if len(stored_key) < len(shortest_key) and key[:len(stored_key)] == stored_key:
                assert False, f"Found shorter prefix {stored_key}"


@given(trie_keys(), st.lists(st.binary(min_size=1, max_size=100), min_size=1, max_size=5))
def test_multiple_values_same_key(key, values):
    """Property: Last value set for a key should be the one retrieved."""
    trie = PyGTrie()
    
    for value in values:
        trie[key] = value
    
    # Should get the last value
    assert trie[key] == values[-1]


@given(st.lists(st.tuples(trie_keys(), st.binary(min_size=1, max_size=100)), min_size=0, max_size=10))
def test_iteration_completeness(items):
    """Property: Iterating over trie should yield all items exactly once."""
    trie = PyGTrie()
    
    # Use dict to handle duplicate keys (last value wins)
    item_dict = {}
    for key, value in items:
        trie[key] = value
        item_dict[key] = value
    
    # Collect all items from iteration
    iterated_items = {key: value for key, value in trie.items()}
    
    assert iterated_items == item_dict


@given(trie_with_items())
def test_shallow_iteration(trie_items):
    """Property: Shallow iteration should skip descendants of nodes with values."""
    trie, _ = trie_items
    
    shallow_items = list(trie.items(shallow=True))
    
    # For each item in shallow iteration, no other item should be its prefix
    for key1, _ in shallow_items:
        for key2, _ in shallow_items:
            if key1 != key2:
                # key2 should not be a proper prefix of key1
                if len(key2) < len(key1) and key1[:len(key2)] == key2:
                    assert False, f"{key2} is a prefix of {key1} in shallow iteration"


@given(trie_keys())
def test_empty_key_access(key):
    """Property: Accessing a non-existent key should raise KeyError."""
    trie = PyGTrie()
    
    with pytest.raises((KeyError, ShortKeyError)):
        _ = trie[key]


@given(trie_keys(), trie_keys(), st.binary(min_size=1, max_size=100))
def test_prefix_error(key1, key2, value):
    """Property: Accessing a key that is only a prefix should raise ShortKeyError."""
    assume(len(key1) < len(key2))
    assume(key2[:len(key1)] == key1)  # key1 is a prefix of key2
    
    trie = PyGTrie()
    trie[key2] = value  # Set the longer key
    
    # Accessing the prefix without a value should raise ShortKeyError
    with pytest.raises(ShortKeyError):
        _ = trie[key1]


if __name__ == "__main__":
    # Run a quick test
    test_round_trip_set_get()
    print("Basic tests passed!")