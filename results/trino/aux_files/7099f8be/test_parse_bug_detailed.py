#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

import trino.auth as auth

# Test the bugs found
def test_empty_value_bug():
    """Demonstrate the IndexError bug with empty values"""
    print("Testing empty value bug...")
    try:
        # This causes IndexError when value is empty string
        header = "key="
        result = auth._OAuth2TokenBearer._parse_authenticate_header(header)
        print(f"Result for 'key=': {result}")
    except IndexError as e:
        print(f"IndexError: {e}")
        print("BUG CONFIRMED: Empty values cause IndexError")
        return True
    return False

def test_value_with_comma_bug():
    """Demonstrate the parsing bug with commas in values"""
    print("\nTesting comma in value bug...")
    # Without quotes, comma in value breaks parsing
    header = "key=value,with,comma"
    result = auth._OAuth2TokenBearer._parse_authenticate_header(header)
    print(f"Result for 'key=value,with,comma': {result}")
    # This gets incorrectly parsed as multiple components
    if 'key' in result and result['key'] != 'value,with,comma':
        print(f"BUG CONFIRMED: Value with comma not parsed correctly: got '{result.get('key')}' instead of 'value,with,comma'")
        return True
    return False

def test_key_with_spaces_bug():
    """Test if keys with spaces are handled correctly"""
    print("\nTesting key with spaces...")
    header = ' key with spaces =value'
    result = auth._OAuth2TokenBearer._parse_authenticate_header(header)
    print(f"Result: {result}")
    # The key gets incorrectly modified
    if 'key with spaces' not in result:
        print(f"BUG CONFIRMED: Key with spaces not preserved correctly")
        return True
    return False

def test_multiple_equals_bug():
    """Test if values with equals signs are handled correctly"""
    print("\nTesting value with equals sign...")
    header = 'key=value=with=equals'
    result = auth._OAuth2TokenBearer._parse_authenticate_header(header)
    print(f"Result for 'key=value=with=equals': {result}")
    if result.get('key') != 'value=with=equals':
        print(f"BUG CONFIRMED: Value with equals not parsed correctly: got '{result.get('key')}' expected 'value=with=equals'")
        return True
    return False

if __name__ == "__main__":
    bugs_found = []
    
    if test_empty_value_bug():
        bugs_found.append("Empty value IndexError")
    
    if test_value_with_comma_bug():
        bugs_found.append("Comma in value parsing")
    
    if test_key_with_spaces_bug():
        bugs_found.append("Key with spaces")
        
    if test_multiple_equals_bug():
        bugs_found.append("Multiple equals in value")
    
    print(f"\n\nTotal bugs found: {len(bugs_found)}")
    for bug in bugs_found:
        print(f"  - {bug}")