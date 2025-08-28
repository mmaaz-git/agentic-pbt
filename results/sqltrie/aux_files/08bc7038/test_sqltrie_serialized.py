import json
from hypothesis import given, strategies as st, assume, settings
from sqltrie import JSONTrie
from sqltrie.pygtrie import PyGTrie


@given(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    )
)
def test_json_round_trip(value):
    """Test that JSON serialization is a proper round-trip"""
    from sqltrie.serialized import json_dumps, json_loads
    
    serialized = json_dumps(value)
    deserialized = json_loads(serialized)
    assert deserialized == value


def trie_key_strategy():
    """Generate valid trie keys"""
    return st.tuples(st.text(min_size=1)).map(tuple)


def multiple_trie_keys_strategy():
    """Generate multiple unique trie keys"""
    return st.lists(
        st.tuples(st.text(min_size=1, max_size=10)),
        min_size=1,
        max_size=5,
        unique=True
    ).map(lambda lst: [tuple(t) for t in lst])


json_value_strategy = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.lists(st.integers(), max_size=10),
    st.dictionaries(st.text(), st.integers(), max_size=5)
)


@given(trie_key_strategy(), json_value_strategy)
def test_jsontrie_set_get_round_trip(key, value):
    """Test that JSONTrie correctly serializes and deserializes values"""
    trie = JSONTrie()
    trie._trie = PyGTrie()
    
    trie[key] = value
    retrieved = trie[key]
    assert retrieved == value


@given(trie_key_strategy())
def test_jsontrie_none_handling(key):
    """Test that JSONTrie correctly handles None values"""
    trie = JSONTrie()
    trie._trie = PyGTrie()
    
    trie[key] = None
    assert trie[key] is None


@given(multiple_trie_keys_strategy())
def test_jsontrie_shortest_prefix(keys):
    """Test shortest_prefix returns correct key"""
    trie = JSONTrie()
    trie._trie = PyGTrie()
    
    # Insert all keys with values
    for i, key in enumerate(keys):
        trie[key] = i
    
    # For each key, test shortest_prefix
    for key in keys:
        result = trie.shortest_prefix(key)
        if result is not None:
            found_key, found_value = result
            # The returned key should be the actual prefix key, not the query key
            assert found_key in keys
            # The value should match what we stored
            assert found_value == keys.index(found_key)
            # It should be a prefix of the query key
            assert key[:len(found_key)] == found_key


@given(multiple_trie_keys_strategy())
def test_jsontrie_longest_prefix(keys):
    """Test longest_prefix returns correct key and value"""
    trie = JSONTrie()
    trie._trie = PyGTrie()
    
    # Insert all keys with values
    for i, key in enumerate(keys):
        trie[key] = i
    
    # For each key, test longest_prefix
    for key in keys:
        result = trie.longest_prefix(key)
        if result is not None:
            found_key, found_value = result
            # The returned key should exist in our keys
            assert found_key in keys
            # The value should match what we stored
            assert found_value == keys.index(found_key)
            # It should be a prefix of the query key
            assert key[:len(found_key)] == found_key


@given(multiple_trie_keys_strategy())
def test_jsontrie_prefixes_iteration(keys):
    """Test that prefixes iteration returns correct keys and values"""
    trie = JSONTrie()
    trie._trie = PyGTrie()
    
    # Insert all keys with values
    for i, key in enumerate(keys):
        trie[key] = i
    
    # For each key, test prefixes
    for key in keys:
        prefixes = list(trie.prefixes(key))
        for prefix_key, prefix_value in prefixes:
            # Each prefix key should exist in our keys
            assert prefix_key in keys
            # The value should match what we stored
            assert prefix_value == keys.index(prefix_key)
            # It should be a prefix of the query key
            assert key[:len(prefix_key)] == prefix_key


@given(st.lists(st.tuples(st.text(min_size=1, max_size=3)), min_size=2, max_size=5))
def test_shortest_prefix_with_extended_keys(key_parts):
    """Test shortest_prefix specifically for the bug where it returns the wrong key"""
    trie = JSONTrie()
    trie._trie = PyGTrie()
    
    # Create a base key and an extended key
    base_key = tuple(key_parts[0])
    extended_key = base_key + tuple(key_parts[1])
    
    # Set values for both
    trie[base_key] = "base"
    trie[extended_key] = "extended"
    
    # Query with the extended key
    result = trie.shortest_prefix(extended_key)
    
    if result is not None:
        returned_key, returned_value = result
        # Bug check: returned_key should be base_key, not extended_key
        assert returned_key == base_key, f"Expected {base_key}, got {returned_key}"
        assert returned_value == "base"


@given(st.lists(st.tuples(st.text(min_size=1, max_size=3)), min_size=2, max_size=5))
def test_shortest_prefix_query_longer_than_stored(key_parts):
    """Test shortest_prefix when querying with a key longer than any stored key"""
    trie = JSONTrie()
    trie._trie = PyGTrie()
    
    # Create a short key
    short_key = tuple(key_parts[0])
    # Create a query key that extends the short key
    query_key = short_key + tuple(key_parts[1])
    
    # Only store the short key
    trie[short_key] = "short"
    
    # Query with the longer key
    result = trie.shortest_prefix(query_key)
    
    if result is not None:
        returned_key, returned_value = result
        # The returned key should be the short_key, not the query_key
        assert returned_key == short_key, f"Bug: shortest_prefix returned {returned_key} instead of {short_key}"
        assert returned_value == "short"