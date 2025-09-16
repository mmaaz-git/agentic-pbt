#!/usr/bin/env python3
"""Potential bug reproduction for parse_yaml_list with escaped quotes."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

import yaml
from copier._user_data import parse_yaml_list

# Bug hypothesis: parse_yaml_list incorrectly handles strings with escaped quotes
# The function strips outer quotes but doesn't handle escaped quotes properly

print("Testing parse_yaml_list with edge cases...")
print("=" * 60)

# Test case 1: String with escaped quotes
yaml_with_escaped = r'''
- "string with \"escaped\" quotes"
- normal
'''

print("Test 1: String with escaped quotes")
print(f"Input YAML: {yaml_with_escaped}")

try:
    result = parse_yaml_list(yaml_with_escaped.strip())
    print(f"Result: {result}")
    
    # The first item should preserve the escaped quotes when stripped
    first_item = result[0]
    print(f"First item raw: '{first_item}'")
    
    # When reparsed, it should handle the escapes correctly
    reparsed = yaml.safe_load(first_item)
    print(f"Reparsed: '{reparsed}'")
    
    # Expected: the reparsed value should be the string with quotes
    # Actual: might fail or produce incorrect result
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "-" * 40 + "\n")

# Test case 2: String that looks like it has quotes but doesn't
yaml_tricky = '''
- '"not actually quoted"'
- regular
'''

print("Test 2: String that looks quoted but isn't")
print(f"Input YAML: {yaml_tricky}")

try:
    result = parse_yaml_list(yaml_tricky.strip())
    print(f"Result: {result}")
    
    first_item = result[0]
    print(f"First item raw: '{first_item}'")
    
    # This might incorrectly strip quotes
    reparsed = yaml.safe_load(first_item)
    print(f"Reparsed: '{reparsed}'")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "-" * 40 + "\n")

# Test case 3: Empty string edge cases
yaml_empty = '''
- ""
- ''
-
- " "
'''

print("Test 3: Empty and whitespace strings")
print(f"Input YAML: {yaml_empty}")

try:
    result = parse_yaml_list(yaml_empty.strip())
    print(f"Result: {result}")
    print(f"Number of items: {len(result)}")
    
    for i, item in enumerate(result):
        print(f"  Item {i}: '{item}' (len={len(item)})")
        try:
            reparsed = yaml.safe_load(item)
            print(f"    Reparsed: {repr(reparsed)}")
        except:
            print(f"    Failed to reparse")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()