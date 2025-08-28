import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sqltrie_env/lib/python3.13/site-packages')

import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import Bundle, RuleBasedStateMachine, rule, initialize, invariant

from sqltrie import SQLiteTrie, PyGTrie, JSONTrie, ShortKeyError
from sqltrie.sqlite import SQLiteTrie as SQLiteTrieImpl


trie_key_element = st.text(min_size=1, max_size=20, alphabet=st.characters(categories=["L", "N"]))
trie_keys = st.lists(trie_key_element, min_size=0, max_size=5).map(tuple)
trie_values = st.binary(min_size=0, max_size=100)


@pytest.fixture(params=[SQLiteTrie, PyGTrie])
def trie_class(request):
    return request.param


class TestBasicProperties:
    
    @given(key=trie_keys, value=trie_values)
    def test_get_set_round_trip_sqlite(self, key, value):
        trie = SQLiteTrie()
        trie[key] = value
        assert trie[key] == value
        trie.close()
    
    @given(key=trie_keys, value=trie_values)
    def test_get_set_round_trip_pygtrie(self, key, value):
        trie = PyGTrie()
        trie[key] = value
        assert trie[key] == value
    
    @given(key=trie_keys)
    def test_delete_raises_keyerror_sqlite(self, key):
        trie = SQLiteTrie()
        assume(key != ())  
        with pytest.raises(KeyError):
            _ = trie[key]
        trie.close()
    
    @given(key=trie_keys, value=trie_values)
    def test_delete_then_get_raises_sqlite(self, key, value):
        trie = SQLiteTrie()
        trie[key] = value
        del trie[key]
        with pytest.raises((KeyError, ShortKeyError)):
            _ = trie[key]
        trie.close()
    
    @given(keys_and_values=st.lists(st.tuples(trie_keys, trie_values), min_size=0, max_size=10))
    def test_items_consistency_sqlite(self, keys_and_values):
        trie = SQLiteTrie()
        expected = {}
        for key, value in keys_and_values:
            trie[key] = value
            expected[key] = value
        
        actual = dict(trie.items())
        assert actual == expected
        trie.close()
    
    @given(keys_and_values=st.lists(st.tuples(trie_keys, trie_values), min_size=0, max_size=10))
    def test_len_invariant_sqlite(self, keys_and_values):
        trie = SQLiteTrie()
        unique_keys = {}
        for key, value in keys_and_values:
            trie[key] = value
            unique_keys[key] = value
        
        assert len(trie) == len(unique_keys)
        trie.close()
    
    @given(parent=trie_keys, child_suffix=st.lists(trie_key_element, min_size=1, max_size=3))
    def test_short_key_error_sqlite(self, parent, child_suffix):
        trie = SQLiteTrie()
        child = parent + tuple(child_suffix)
        trie[child] = b"child_value"
        
        with pytest.raises(ShortKeyError):
            _ = trie[parent]
        trie.close()
    
    @given(parent=trie_keys, child_suffix=st.lists(trie_key_element, min_size=1, max_size=3))
    def test_short_key_error_pygtrie(self, parent, child_suffix):
        trie = PyGTrie()
        child = parent + tuple(child_suffix)
        trie[child] = b"child_value"
        
        with pytest.raises(ShortKeyError):
            _ = trie[parent]


class TestPrefixProperties:
    
    @given(
        keys_and_values=st.lists(st.tuples(trie_keys, trie_values), min_size=1, max_size=10),
        query_key=trie_keys
    )
    def test_shortest_prefix_sqlite(self, keys_and_values, query_key):
        trie = SQLiteTrie()
        for key, value in keys_and_values:
            trie[key] = value
        
        result = trie.shortest_prefix(query_key)
        
        if result is not None:
            prefix_key, prefix_value = result
            assert len(prefix_key) <= len(query_key)
            assert query_key[:len(prefix_key)] == prefix_key
            assert trie[prefix_key] == prefix_value
            
            for key, _ in keys_and_values:
                if len(key) < len(prefix_key) and query_key[:len(key)] == key:
                    assert False, f"Found shorter prefix {key} than {prefix_key}"
        trie.close()
    
    @given(
        keys_and_values=st.lists(st.tuples(trie_keys, trie_values), min_size=1, max_size=10),
        query_key=trie_keys
    )
    def test_longest_prefix_sqlite(self, keys_and_values, query_key):
        trie = SQLiteTrie()
        for key, value in keys_and_values:
            trie[key] = value
        
        result = trie.longest_prefix(query_key)
        
        if result is not None:
            prefix_key, prefix_value = result
            assert len(prefix_key) <= len(query_key)
            assert query_key[:len(prefix_key)] == prefix_key
            assert trie[prefix_key] == prefix_value
            
            for key, _ in keys_and_values:
                if len(key) > len(prefix_key) and len(key) <= len(query_key) and query_key[:len(key)] == key:
                    assert False, f"Found longer prefix {key} than {prefix_key}"
        trie.close()


class TestViewProperties:
    
    @given(
        prefix=trie_keys,
        suffixes_and_values=st.lists(st.tuples(trie_keys, trie_values), min_size=0, max_size=10)
    )
    def test_view_isolation_sqlite(self, prefix, suffixes_and_values):
        trie = SQLiteTrie()
        
        for suffix, value in suffixes_and_values:
            full_key = prefix + suffix
            trie[full_key] = value
        
        trie[('other', 'key')] = b"should_not_appear"
        
        view = trie.view(prefix)
        view_items = dict(view.items())
        
        for suffix, value in suffixes_and_values:
            if suffix in view_items:
                assert view_items[suffix] == value
        
        assert ('other', 'key') not in view_items
        assert ('other',) not in view_items
        trie.close()


class TestJSONTrieProperties:
    
    @given(
        key=trie_keys,
        value=st.one_of(
            st.none(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(max_size=50),
            st.lists(st.integers(), max_size=10),
            st.dictionaries(st.text(max_size=10), st.integers(), max_size=5)
        )
    )
    def test_json_round_trip(self, key, value):
        base_trie = SQLiteTrie()
        trie = JSONTrie()
        trie._trie = base_trie
        
        trie[key] = value
        retrieved = trie[key]
        
        if value is None:
            assert retrieved is None
        elif isinstance(value, (int, str)):
            assert retrieved == value
        elif isinstance(value, float):
            import math
            assert math.isclose(retrieved, value, rel_tol=1e-9)
        elif isinstance(value, (list, dict)):
            assert retrieved == value
        
        base_trie.close()


class TestHasNodeProperty:
    
    @given(parent=trie_keys, child_suffix=st.lists(trie_key_element, min_size=1, max_size=3))
    def test_has_node_vs_has_value_sqlite(self, parent, child_suffix):
        trie = SQLiteTrie()
        child = parent + tuple(child_suffix)
        trie[child] = b"value"
        
        assert trie.has_node(child)
        
        assert trie.has_node(parent)
        
        assert child in trie
        assert parent not in trie
        trie.close()


class TestStatefulTrie(RuleBasedStateMachine):
    
    def __init__(self):
        super().__init__()
        self.trie = SQLiteTrie()
        self.model = {}
    
    @initialize()
    def setup(self):
        self.trie = SQLiteTrie()
        self.model = {}
    
    @rule(key=trie_keys, value=trie_values)
    def set_item(self, key, value):
        self.trie[key] = value
        self.model[key] = value
    
    @rule(key=st.sampled_from(Bundle("existing_keys")))
    def delete_item(self, key):
        if key in self.model:
            del self.trie[key]
            del self.model[key]
    
    @rule()
    def check_consistency(self):
        trie_items = dict(self.trie.items())
        assert trie_items == self.model
        assert len(self.trie) == len(self.model)
    
    def teardown(self):
        self.trie.close()


TestStatefulTrieExecution = TestStatefulTrie.TestCase
TestStatefulTrieExecution.settings = settings(max_examples=50)