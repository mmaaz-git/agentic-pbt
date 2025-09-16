#!/usr/bin/env python3
import sys
import os
import tempfile

# Add site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/sqltrie_env/lib/python3.13/site-packages')

from sqltrie import SQLiteTrie, PyGTrie, ShortKeyError

print("="*60)
print("BUG ROOT CAUSE ANALYSIS")
print("="*60)

# Bug 1: Empty string handling - deeper analysis
print("\nBug 1: Empty String Handling")
print("-"*30)

with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
    db_path = f.name

try:
    trie = SQLiteTrie.open(db_path)
    
    # Test different empty string combinations
    test_cases = [
        (('',), b'single_empty'),
        (('', ''), b'double_empty'),
        (('a', ''), b'normal_then_empty'),
        (('', 'b'), b'empty_then_normal'),
    ]
    
    for key, value in test_cases:
        try:
            print(f"Setting {key!r} = {value!r}... ", end="")
            trie[key] = value
            print("OK, Getting... ", end="")
            result = trie[key]
            print(f"OK: {result!r}")
        except Exception as e:
            print(f"FAILED: {type(e).__name__}: {e}")
    
    trie.close()
finally:
    os.unlink(db_path)

# Bug 2: Path construction issue
print("\nBug 2: SQL Path Construction Issue")  
print("-"*30)

with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
    db_path = f.name

try:
    trie = SQLiteTrie.open(db_path)
    
    print("The issue is in _traverse() method which constructs SQL paths")
    print("It uses '/'.join(key) which creates issues with:")
    print("1. Empty strings - results in '//' in path")
    print("2. Null characters - embedded in SQL string")
    
    # Show the problematic line
    print("\nProblematic code in sqlite.py line 190:")
    print("  path = '/'.join(key).replace(\"'\", \"''\")")
    print("  self._conn.executescript(STEPS_SQL.format(path=path, root=self._root_id))")
    
    print("\nWith key=('', ''), path becomes: ''")
    print("With key=('\\x00',), path contains null character")
    
    trie.close()
finally:
    os.unlink(db_path)

# Bug 3: ShortKeyError semantics
print("\nBug 3: ShortKeyError Semantics")
print("-"*30)

with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
    db_path = f.name

try:
    trie = SQLiteTrie.open(db_path)
    
    print("Testing ShortKeyError behavior:")
    
    # Set and delete root
    trie[()] = b'root'
    print("1. Set root node: trie[()] = b'root'")
    
    del trie[()]
    print("2. Deleted root node: del trie[()]")
    
    # Check has_node vs __getitem__
    print(f"3. has_node(()): {trie.has_node(())}")
    
    try:
        val = trie[()]
        print(f"4. trie[()]: {val!r}")
    except ShortKeyError as e:
        print(f"4. trie[()] raises ShortKeyError (should be KeyError)")
        print("   ShortKeyError should only occur when node exists but has no value")
        print("   After deletion, it should raise KeyError instead")
    except KeyError as e:
        print(f"4. trie[()] correctly raises KeyError")
    
    trie.close()
finally:
    os.unlink(db_path)