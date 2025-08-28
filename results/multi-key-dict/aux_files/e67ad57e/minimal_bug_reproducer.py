#!/usr/bin/env python3
"""
Minimal reproducers for potential bugs in multi_key_dict
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/multi-key-dict_env/lib/python3.13/site-packages')

import multi_key_dict

print("Testing potential bugs in multi_key_dict")
print("=" * 60)

# Bug 1: Boolean/Integer key collision
print("\nBug 1: Boolean vs Integer keys (True == 1 in Python)")
print("-" * 50)
try:
    m = multi_key_dict.multi_key_dict()
    
    # First, set True with 'a' as multi-keys
    m[True, 'a'] = 'bool_value'
    print(f"Set m[True, 'a'] = 'bool_value'")
    print(f"  m[True] = {m[True]}")
    print(f"  m[1] = {m[1]}")  # True == 1 in Python
    print(f"  m['a'] = {m['a']}")
    
    # Now try to set 1 with 'b' as multi-keys  
    # This should fail because 1 already maps to a value (since True == 1)
    print("\nTrying to set m[1, 'b'] = 'int_value'...")
    try:
        m[1, 'b'] = 'int_value'
        print("  SUCCESS - but this might be a bug!")
        print(f"  m[1] = {m[1]}")
        print(f"  m['b'] = {m['b']}")
    except KeyError as e:
        print(f"  KeyError raised (expected): {e}")
        
except Exception as e:
    print(f"  Unexpected error: {e}")

# Bug 2: Type coercion in internal dictionary keys
print("\n\nBug 2: Type name collision in internal storage")
print("-" * 50)
try:
    m = multi_key_dict.multi_key_dict()
    
    # The implementation uses str(type(key)) as internal dict keys
    # This could cause issues with certain key values
    
    # Try using the string "<class 'int'>" as a key
    type_str = str(type(1))  # This will be "<class 'int'>"
    print(f"str(type(1)) = '{type_str}'")
    
    m[type_str, 'normal'] = 'value1'
    print(f"Set m['{type_str}', 'normal'] = 'value1'")
    
    # Now add an integer key
    m[42] = 'value2'
    print(f"Set m[42] = 'value2'")
    
    # Check internal structure (this accesses private implementation)
    if hasattr(m, '__dict__'):
        internal_keys = [k for k in m.__dict__.keys() if k.startswith("<class")]
        print(f"Internal dictionary keys: {internal_keys}")
        
except Exception as e:
    print(f"  Error: {e}")

# Bug 3: Empty keys list
print("\n\nBug 3: Empty tuple/list as keys")
print("-" * 50)
try:
    m = multi_key_dict.multi_key_dict()
    
    # Try setting with empty tuple
    print("Trying m[()] = 'empty'...")
    try:
        m[()] = 'empty'
        print("  SUCCESS - Empty tuple accepted (potential bug!)")
        print(f"  Length of dictionary: {len(m)}")
    except Exception as e:
        print(f"  Correctly rejected: {e}")
    
    # Try with empty list
    print("\nTrying m[[]] = 'empty'...")
    try:
        m[[]] = 'empty'
        print("  SUCCESS - Empty list accepted (potential bug!)")
    except Exception as e:
        print(f"  Correctly rejected: {e}")
        
except Exception as e:
    print(f"  Error: {e}")

# Bug 4: Duplicate keys in the keys tuple
print("\n\nBug 4: Duplicate keys in multi-key mapping")
print("-" * 50)
try:
    m = multi_key_dict.multi_key_dict()
    
    # Set with duplicate keys
    m['a', 'a', 'b'] = 'duplicates'
    print("Set m['a', 'a', 'b'] = 'duplicates'")
    
    print(f"  m['a'] = {m['a']}")
    print(f"  m['b'] = {m['b']}")
    
    # Check get_other_keys
    others = m.get_other_keys('a')
    print(f"  get_other_keys('a') = {others}")
    
    # Count occurrences of 'a' in other keys
    a_count = others.count('a')
    if a_count > 0:
        print(f"  BUG: 'a' appears {a_count} time(s) in its own other_keys!")
    else:
        print("  OK: 'a' doesn't appear in its other_keys")
        
    # Check with including_current=True
    all_keys = m.get_other_keys('a', including_current=True)
    print(f"  get_other_keys('a', True) = {all_keys}")
    a_count_all = all_keys.count('a')
    print(f"  'a' appears {a_count_all} time(s) in all_keys")
    
except Exception as e:
    print(f"  Error: {e}")

# Bug 5: Update semantics with partial key overlap
print("\n\nBug 5: Partial key overlap in multi-key mappings")
print("-" * 50)
try:
    m = multi_key_dict.multi_key_dict()
    
    # First mapping
    m['a', 'b', 'c'] = 'first'
    print("Set m['a', 'b', 'c'] = 'first'")
    
    # Try to create new mapping with partial overlap
    print("Trying m['b', 'c', 'd'] = 'second'...")
    try:
        m['b', 'c', 'd'] = 'second'
        print("  SUCCESS - Partial overlap allowed (potential bug!)")
        print(f"  m['a'] = {m['a']}")
        print(f"  m['b'] = {m['b']}")
        print(f"  m['c'] = {m['c']}")
        print(f"  m['d'] = {m['d']}")
    except KeyError as e:
        print(f"  Correctly rejected: {e}")
        
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "=" * 60)
print("Bug reproduction completed!")
print("=" * 60)