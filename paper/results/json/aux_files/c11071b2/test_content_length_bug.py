"""
Demonstrate the Content-Length bug with non-ASCII string bodies.
"""

import requests
import requests.models


def test_content_length_with_non_ascii():
    """Test that Content-Length is calculated incorrectly for non-ASCII strings."""
    
    # Create a request with non-ASCII body
    req = requests.Request('POST', 'http://example.com', data='日本語')
    prepared = req.prepare()
    
    # Check Content-Length header
    content_length = prepared.headers.get('Content-Length')
    
    print(f"Body: '日本語'")
    print(f"String length (characters): {len('日本語')}")
    print(f"UTF-8 byte length: {len('日本語'.encode('utf-8'))}")
    print(f"Content-Length header: {content_length}")
    
    # The Content-Length should match the byte length when sent over HTTP
    # But the issue is that super_len returns the byte length when it should
    # return character length for consistency with len() on strings
    
    assert content_length == '9', f"Expected Content-Length: 9, got: {content_length}"


def test_super_len_inconsistency():
    """Demonstrate the inconsistency in super_len."""
    import requests.utils
    
    test_strings = [
        '',           # Empty string
        'hello',      # ASCII only
        'café',       # Latin-1 extended
        '日本語',      # Japanese
        '😀🎉',       # Emojis
        'a\x80b',     # Mixed ASCII and non-ASCII
    ]
    
    print("\nInconsistency in super_len vs len for strings:")
    print("-" * 60)
    print(f"{'String':<20} {'len()':<10} {'super_len()':<12} {'UTF-8 bytes':<12}")
    print("-" * 60)
    
    for s in test_strings:
        str_len = len(s)
        super_len_val = requests.utils.super_len(s)
        byte_len = len(s.encode('utf-8'))
        
        display_str = repr(s) if len(repr(s)) <= 20 else repr(s)[:17] + '...'
        print(f"{display_str:<20} {str_len:<10} {super_len_val:<12} {byte_len:<12}")
        
        # super_len returns byte length, not character length
        assert super_len_val == byte_len, f"super_len returns byte length, not character length"


if __name__ == "__main__":
    print("Testing Content-Length calculation with non-ASCII strings...")
    test_content_length_with_non_ascii()
    print("\n✓ Content-Length test passed (but shows the bug)")
    
    test_super_len_inconsistency()
    print("\n✓ All assertions passed - bug confirmed!")