"""
Test demonstrating bug in requests.utils.super_len with non-ASCII strings.
"""

import requests.utils
from hypothesis import given, strategies as st, settings


@given(st.text())
@settings(max_examples=1000)
def test_super_len_string_length(s):
    """Test that super_len returns correct length for strings."""
    length = requests.utils.super_len(s)
    
    # When is_urllib3_1 is False (urllib3 2.x+), strings are encoded as UTF-8
    # But super_len should still return the logical string length, not byte length
    expected_length = len(s)
    
    assert length == expected_length, (
        f"super_len returned {length} but string has {expected_length} characters. "
        f"String: {repr(s)}"
    )


if __name__ == "__main__":
    # Minimal reproduction
    print("Testing super_len bug with non-ASCII characters...")
    
    test_cases = [
        '\x80',  # Single non-ASCII character
        'a\x80b',  # ASCII + non-ASCII
        '日本語',  # Japanese characters  
        '😀',  # Emoji
        'résumé',  # Accented characters
    ]
    
    for test_str in test_cases:
        actual = requests.utils.super_len(test_str)
        expected = len(test_str)
        
        if actual != expected:
            print(f"✗ FAIL: {repr(test_str)}")
            print(f"  Expected length: {expected}")
            print(f"  Actual length: {actual}")
            print(f"  UTF-8 byte length: {len(test_str.encode('utf-8'))}")
        else:
            print(f"✓ PASS: {repr(test_str)} (length={expected})")
    
    print("\nRunning property-based test...")
    import pytest
    pytest.main([__file__, "-v"])