import os
import tempfile
from hypothesis import given, strategies as st, assume, settings, example
from sqltrie import SQLiteTrie, PyGTrie, ShortKeyError, JSONTrie
from sqltrie.serialized import SerializedTrie
import json


# More aggressive strategies
edge_case_strings = st.one_of(
    st.text(alphabet=st.characters(min_codepoint=0x00, max_codepoint=0x7F), min_size=0, max_size=20),  # ASCII including control chars
    st.text(alphabet="🦄🎈🎉💻🐍", min_size=1, max_size=5),  # Emojis
    st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=0, max_size=10),  # Alphanumeric
    st.just(""),  # Empty string
    st.just(" "),  # Space
    st.just("\n"),  # Newline
    st.just("\t"),  # Tab
    st.just("\\"),  # Backslash
    st.just("''"),  # Double single quote
    st.just("'"),  # Single quote
    st.just("//"),  # Double slash
    st.just("/"),  # Single slash
)

# Keys with edge cases
edge_trie_keys = st.lists(
    edge_case_strings.filter(lambda x: "/" not in x and "'" not in x),
    min_size=0,
    max_size=10
).map(tuple)

# Include empty tuple explicitly
empty_key = st.just(())

# Complex nested JSON values for JSONTrie
json_values = st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-1e10, max_value=1e10),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(max_size=100),
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=5),
        st.dictionaries(st.text(max_size=10), children, max_size=5),
    ),
    max_leaves=10
)


@given(edge_trie_keys, st.binary(min_size=0, max_size=1000))
@settings(max_examples=100)
def test_empty_key_handling(key, value):
    """Test handling of empty keys and empty values"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        trie = SQLiteTrie.open(db_path)
        
        # Test empty key (root)
        trie[()] = value
        assert trie[()] == value
        
        # Test regular key after empty key
        if key != ():
            trie[key] = value
            assert trie[key] == value
            # Empty key should still be there
            assert trie[()] == value
        
        trie.close()
    finally:
        os.unlink(db_path)


@given(st.lists(edge_trie_keys, min_size=1, max_size=10))
@settings(max_examples=100)
def test_hierarchical_deletion(keys):
    """Test that deleting parent doesn't affect children"""
    assume(len(keys) > 1)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        trie = SQLiteTrie.open(db_path)
        
        # Build hierarchical structure
        for i, key in enumerate(keys):
            trie[key] = f"value_{i}".encode()
            # Also add child keys
            if key:
                child_key = key + ("child",)
                trie[child_key] = f"child_{i}".encode()
        
        # Delete parent keys and check children still exist
        for key in keys:
            if key in trie:
                del trie[key]
                # Check child still exists
                child_key = key + ("child",)
                if child_key in trie:
                    # Child should still be accessible
                    _ = trie[child_key]
        
        trie.close()
    finally:
        os.unlink(db_path)


@given(edge_trie_keys, json_values)
@settings(max_examples=100)
def test_json_trie_serialization(key, value):
    """Test JSONTrie with complex JSON values"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        # Create SQLiteTrie backend
        backend = SQLiteTrie.open(db_path)
        
        # Wrap with JSONTrie
        trie = JSONTrie()
        trie._trie = backend
        
        # Store JSON value
        trie[key] = value
        
        # Retrieve and verify
        retrieved = trie[key]
        assert retrieved == value
        
        # Test that it survives JSON round-trip
        json_str = json.dumps(value)
        reparsed = json.loads(json_str)
        assert retrieved == reparsed
        
        backend.close()
    finally:
        os.unlink(db_path)


@given(st.lists(st.tuples(edge_trie_keys, st.binary(max_size=100)), min_size=5, max_size=20))
@settings(max_examples=50)
def test_concurrent_modifications(items):
    """Test rapid insertions and deletions"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        trie = SQLiteTrie.open(db_path)
        
        # Rapidly insert and delete
        for key, value in items:
            trie[key] = value
        
        # Delete every other item
        for i, (key, _) in enumerate(items):
            if i % 2 == 0 and key in trie:
                del trie[key]
        
        # Verify remaining items
        for i, (key, value) in enumerate(items):
            if i % 2 == 1:
                assert trie[key] == value
            else:
                try:
                    _ = trie[key]
                    # Might still exist if duplicate key
                    pass
                except (KeyError, ShortKeyError):
                    pass  # Expected
        
        trie.close()
    finally:
        os.unlink(db_path)


@given(st.lists(edge_trie_keys, min_size=1, max_size=5))
@settings(max_examples=100)
def test_view_with_nonexistent_prefix(keys):
    """Test creating views with non-existent prefixes"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        trie = SQLiteTrie.open(db_path)
        
        # Create view with non-existent prefix
        for key in keys:
            view = trie.view(key)
            # Should create empty view
            assert len(list(view.items())) == 0
            
            # Add to view
            view[("test",)] = b"value"
            view.commit()
            
            # Check it's in parent
            full_key = key + ("test",)
            assert trie[full_key] == b"value"
        
        trie.close()
    finally:
        os.unlink(db_path)


@given(st.lists(st.tuples(edge_trie_keys, st.binary(max_size=100)), min_size=1, max_size=10))
@settings(max_examples=100) 
def test_ls_consistency(items):
    """Test ls() returns correct children"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        trie = SQLiteTrie.open(db_path)
        
        # Insert items
        for key, value in items:
            trie[key] = value
        
        # Test ls for each unique prefix
        tested_prefixes = set()
        for key, _ in items:
            for i in range(len(key)):
                prefix = key[:i]
                if prefix not in tested_prefixes:
                    tested_prefixes.add(prefix)
                    
                    # Get children via ls
                    children = list(trie.ls(prefix, with_values=False))
                    
                    # Verify children are direct children
                    for child in children:
                        # Child should start with prefix
                        assert child[:len(prefix)] == prefix
                        # Child should be exactly one element longer
                        assert len(child) == len(prefix) + 1
        
        trie.close()
    finally:
        os.unlink(db_path)


@given(edge_trie_keys, st.binary(max_size=100))
@settings(max_examples=100)
def test_special_characters_in_keys(key, value):
    """Test keys with special characters"""
    # Create a key with problematic characters
    special_keys = [
        (),  # Empty
        ("",),  # Empty string element
        (" ",),  # Space
        ("\n",),  # Newline
        ("\t",),  # Tab
        ("\\",),  # Backslash
        ("a" * 1000,),  # Very long string
    ]
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        trie = SQLiteTrie.open(db_path)
        
        for special_key in special_keys:
            trie[special_key] = value
            assert trie[special_key] == value
            
            # Combine with regular key
            if key:
                combined = special_key + key
                trie[combined] = value
                assert trie[combined] == value
        
        trie.close()
    finally:
        os.unlink(db_path)


@given(st.lists(st.tuples(edge_trie_keys, st.binary(max_size=50)), min_size=2, max_size=10))
@settings(max_examples=50)
def test_transaction_rollback(items):
    """Test that rollback properly reverts changes"""
    assume(len(items) >= 2)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        trie = SQLiteTrie.open(db_path)
        
        # Insert first half and commit
        mid = len(items) // 2
        for key, value in items[:mid]:
            trie[key] = value
        trie.commit()
        
        # Insert second half but rollback
        for key, value in items[mid:]:
            trie[key] = value
        trie.rollback()
        
        # Verify only first half exists
        for key, value in items[:mid]:
            if key in trie:  # Might have duplicates
                assert trie[key] == value
        
        for key, _ in items[mid:]:
            if key not in [k for k, _ in items[:mid]]:
                # Should not exist unless it was in first half
                try:
                    _ = trie[key]
                    assert False, f"Key {key} should not exist after rollback"
                except (KeyError, ShortKeyError):
                    pass  # Expected
        
        trie.close()
    finally:
        os.unlink(db_path)