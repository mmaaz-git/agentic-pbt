#!/usr/bin/env python3
import sys
import os
import tempfile
import traceback

# Add site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/sqltrie_env/lib/python3.13/site-packages')

from sqltrie import SQLiteTrie, PyGTrie, ShortKeyError

print("="*60)
print("BUG REPRODUCTION SCRIPTS")
print("="*60)

def test_bug(bug_name, test_func):
    print(f"\n{bug_name}")
    print("-"*len(bug_name))
    try:
        test_func()
        print("✓ No bug found")
    except Exception as e:
        print(f"✗ BUG CONFIRMED: {type(e).__name__}: {e}")
        traceback.print_exc()
    print()

# Bug 1: Empty string in key causes KeyError
def bug1_empty_string_key():
    """Keys containing empty strings fail"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        trie = SQLiteTrie.open(db_path)
        
        # This should work according to the API
        key = ('', '')
        value = b'test'
        
        print(f"Setting trie[{key!r}] = {value!r}")
        trie[key] = value
        
        print(f"Getting trie[{key!r}]")
        result = trie[key]
        print(f"Result: {result!r}")
        
        trie.close()
    finally:
        os.unlink(db_path)

# Bug 2: Null character causes ValueError
def bug2_null_character():
    """Keys containing null characters cause ValueError"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        trie = SQLiteTrie.open(db_path)
        
        # Key with null character
        key = ('\x00',)
        
        print(f"Creating view with key containing null character: {key!r}")
        view = trie.view(key)
        
        trie.close()
    finally:
        os.unlink(db_path)

# Bug 3: ShortKeyError on empty tuple after modifications
def bug3_empty_tuple_shortkey():
    """Empty tuple raises ShortKeyError in certain contexts"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        trie = SQLiteTrie.open(db_path)
        
        # Set value at root
        trie[()] = b'root_value'
        print(f"Set trie[()] = b'root_value'")
        
        # This works
        print(f"Getting trie[()]: {trie[()]!r}")
        
        # Now delete it
        del trie[()]
        print("Deleted trie[()]")
        
        # Try to access it again - should raise KeyError, not ShortKeyError
        print("Attempting to get trie[()] after deletion...")
        result = trie[()]
        print(f"Result: {result!r}")
        
        trie.close()
    finally:
        os.unlink(db_path)

# Bug 4: ls() fails with empty string keys
def bug4_ls_empty_string():
    """ls() fails when trying to list children of keys with empty strings"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        trie = SQLiteTrie.open(db_path)
        
        # Create a key path with empty strings
        key = ('', '', 'test')
        trie[key] = b'value'
        print(f"Set trie[{key!r}] = b'value'")
        
        # Try to list children at prefix with empty strings
        prefix = ('', '')
        print(f"Listing children at prefix {prefix!r}")
        children = list(trie.ls(prefix))
        print(f"Children: {children}")
        
        trie.close()
    finally:
        os.unlink(db_path)

# Bug 5: Comparison with PyGTrie
def bug5_implementation_difference():
    """SQLiteTrie and PyGTrie behave differently for edge cases"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        sqlite_trie = SQLiteTrie.open(db_path)
        pyg_trie = PyGTrie()
        
        # Test with empty string key
        key = ('', 'test')
        value = b'value'
        
        print(f"Testing key {key!r} with value {value!r}")
        
        # PyGTrie handles it fine
        pyg_trie[key] = value
        print(f"PyGTrie: Set successfully")
        pyg_result = pyg_trie[key]
        print(f"PyGTrie: Get result = {pyg_result!r}")
        
        # SQLiteTrie might fail
        sqlite_trie[key] = value
        print(f"SQLiteTrie: Set successfully")
        sqlite_result = sqlite_trie[key]
        print(f"SQLiteTrie: Get result = {sqlite_result!r}")
        
        assert sqlite_result == pyg_result, "Results differ!"
        
        sqlite_trie.close()
    finally:
        os.unlink(db_path)

# Run all bug reproductions
test_bug("Bug 1: Empty string in key causes KeyError", bug1_empty_string_key)
test_bug("Bug 2: Null character causes ValueError", bug2_null_character)
test_bug("Bug 3: ShortKeyError on empty tuple after deletion", bug3_empty_tuple_shortkey)
test_bug("Bug 4: ls() fails with empty string keys", bug4_ls_empty_string)
test_bug("Bug 5: SQLiteTrie vs PyGTrie implementation difference", bug5_implementation_difference)