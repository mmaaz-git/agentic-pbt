"""Run property-based tests manually."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.scripts.common import parse_vars
import traceback

def test_basic():
    """Test basic functionality."""
    print("Testing basic parse_vars...")
    
    # Test 1: Simple case
    result = parse_vars(['a=b'])
    assert result == {'a': 'b'}, f"Expected {{'a': 'b'}}, got {result}"
    print("✓ Simple case works")
    
    # Test 2: Multiple equals in value
    result = parse_vars(['key=val=with=equals'])
    assert result == {'key': 'val=with=equals'}, f"Expected value with equals, got {result}"
    print("✓ Multiple equals in value works")
    
    # Test 3: Empty value
    result = parse_vars(['key='])
    assert result == {'key': ''}, f"Expected empty value, got {result}"
    print("✓ Empty value works")
    
    # Test 4: Empty key
    result = parse_vars(['=value'])
    assert result == {'': 'value'}, f"Expected empty key, got {result}"
    print("✓ Empty key works")
    
    # Test 5: No equals should raise error
    try:
        result = parse_vars(['noequals'])
        print("✗ Should have raised ValueError for no equals")
        return False
    except ValueError as e:
        print(f"✓ Correctly raised error: {e}")
    
    # Test 6: Multiple variables
    result = parse_vars(['a=1', 'b=2', 'c=3'])
    assert result == {'a': '1', 'b': '2', 'c': '3'}, f"Expected multiple vars, got {result}"
    print("✓ Multiple variables work")
    
    # Test 7: Duplicate keys - last should win
    result = parse_vars(['key=first', 'key=second'])
    assert result == {'key': 'second'}, f"Expected last value to win, got {result}"
    print("✓ Duplicate keys - last wins")
    
    return True

def test_edge_cases():
    """Test edge cases with special characters."""
    print("\nTesting edge cases...")
    
    # Test with spaces
    result = parse_vars(['key with spaces=value with spaces'])
    assert result == {'key with spaces': 'value with spaces'}
    print("✓ Spaces in keys and values work")
    
    # Test with special characters
    result = parse_vars(['key-with-dash=value'])
    assert result == {'key-with-dash': 'value'}
    print("✓ Dashes work")
    
    # Test with unicode
    result = parse_vars(['unicode🦄=emoji🎉'])
    assert result == {'unicode🦄': 'emoji🎉'}
    print("✓ Unicode/emoji work")
    
    # Test with newlines in value
    result = parse_vars(['key=value\nwith\nnewlines'])
    assert result == {'key': 'value\nwith\nnewlines'}
    print("✓ Newlines in value work")
    
    # Test with tabs
    result = parse_vars(['key\twith\ttabs=value\twith\ttabs'])
    assert result == {'key\twith\ttabs': 'value\twith\ttabs'}
    print("✓ Tabs work")
    
    return True

def test_round_trip():
    """Test round-trip property."""
    print("\nTesting round-trip property...")
    
    test_cases = [
        {'simple': 'value'},
        {'key': 'value=with=equals'},
        {'': 'empty_key'},
        {'empty_value': ''},
        {'unicode🦄': 'emoji🎉'},
        {'key with spaces': 'value with spaces'},
        {'a': '1', 'b': '2', 'c': '3'}
    ]
    
    for original in test_cases:
        input_list = [f"{k}={v}" for k, v in original.items()]
        result = parse_vars(input_list)
        assert result == original, f"Round-trip failed: {original} != {result}"
        print(f"✓ Round-trip works for {original}")
    
    return True

if __name__ == "__main__":
    try:
        success = True
        success = test_basic() and success
        success = test_edge_cases() and success
        success = test_round_trip() and success
        
        if success:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)