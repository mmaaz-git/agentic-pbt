#!/usr/bin/env python3
"""
Test that confirms a bug in multi_key_dict with duplicate keys
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/multi-key-dict_env/lib/python3.13/site-packages')

import multi_key_dict

print("=" * 70)
print("CONFIRMED BUG TEST: Duplicate keys in multi-key mapping")
print("=" * 70)

# Create a multi_key_dict
m = multi_key_dict.multi_key_dict()

# Set a value with duplicate keys
print("\nSetting m['a', 'a', 'b'] = 'test_value'")
m['a', 'a', 'b'] = 'test_value'

# Test basic retrieval
print(f"m['a'] = {m['a']}")  # Should work
print(f"m['b'] = {m['b']}")  # Should work

# Test get_other_keys - THIS IS WHERE THE BUG IS
print("\nTesting get_other_keys('a'):")
other_keys = m.get_other_keys('a')
print(f"Result: {other_keys}")
print(f"Type: {type(other_keys)}")

# Analysis
print("\nBUG ANALYSIS:")
if 'a' in other_keys:
    print("✗ BUG CONFIRMED: 'a' appears in its own get_other_keys() result!")
    print("  This violates the method's contract - it should return OTHER keys only.")
    a_count = other_keys.count('a')
    print(f"  'a' appears {a_count} time(s) in the result")
else:
    print("✓ No bug - 'a' correctly excluded from other_keys")

# Test with including_current=True
print("\nTesting get_other_keys('a', including_current=True):")
all_keys = m.get_other_keys('a', including_current=True)
print(f"Result: {all_keys}")
a_count = all_keys.count('a')
print(f"'a' appears {a_count} time(s) (expected: 2 times due to duplicate)")

# Additional test with 'b'
print("\nTesting get_other_keys('b'):")
other_keys_b = m.get_other_keys('b')
print(f"Result: {other_keys_b}")
expected_for_b = ['a', 'a']  # Should have two 'a's
if other_keys_b.count('a') != 2:
    print(f"✗ Issue: Expected 2 occurrences of 'a', got {other_keys_b.count('a')}")

print("\n" + "=" * 70)
print("BUG REPRODUCTION COMPLETE")
print("=" * 70)

# Demonstrate the root cause
print("\nROOT CAUSE ANALYSIS:")
print("In get_other_keys() at line 173-175:")
print("  other_keys.extend(self.__dict__[str(type(key))][key])")
print("  if not including_current:")
print("      other_keys.remove(key)")
print("")
print("The issue: When keys tuple is ('a', 'a', 'b'), calling")
print("get_other_keys('a') extends other_keys with ['a', 'a', 'b'],")
print("then removes only ONE occurrence of 'a', leaving one 'a' in the result.")
print("")
print("This violates the documented behavior that get_other_keys returns")
print("'other keys' - 'a' is not an 'other' key to itself!")

# Create minimal standalone reproducer
print("\n" + "=" * 70)
print("MINIMAL STANDALONE REPRODUCER:")
print("=" * 70)
print("""
import multi_key_dict

m = multi_key_dict.multi_key_dict()
m['a', 'a', 'b'] = 'value'
result = m.get_other_keys('a')
assert 'a' not in result, f"Bug: 'a' found in get_other_keys('a'): {result}"
""")