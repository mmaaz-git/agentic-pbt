"""Focused test for escape_uri_path bug."""

import django.utils.encoding
from hypothesis import given, strategies as st


# Test that demonstrates the bug more clearly
@given(st.text(alphabet=st.characters(categories=['L', 'N']) | st.sampled_from(['%', ' ', '/', '-', '_'])))
def test_escape_uri_path_not_idempotent(text):
    """Test that escape_uri_path is not idempotent - a clear bug."""
    # First escape
    escaped_once = django.utils.encoding.escape_uri_path(text)
    
    # Second escape should ideally return the same result (idempotent)
    # But it doesn't - it escapes the % signs from the first escape
    escaped_twice = django.utils.encoding.escape_uri_path(escaped_once)
    
    # If the function was idempotent, these should be equal
    # But they're not when text contains characters that need escaping
    if '%' in text or ' ' in text:
        # These will definitely cause double-escaping
        assert escaped_once != escaped_twice, f"Expected double-escaping for {repr(text)}"
        
        # The string grows each time
        assert len(escaped_twice) > len(escaped_once)
        
        # Third escape makes it even worse
        escaped_thrice = django.utils.encoding.escape_uri_path(escaped_twice)
        assert len(escaped_thrice) > len(escaped_twice)
        
        print(f"Bug confirmed for input {repr(text)}:")
        print(f"  Once: {repr(escaped_once)}")
        print(f"  Twice: {repr(escaped_twice)}")
        print(f"  Thrice: {repr(escaped_thrice)}")


if __name__ == "__main__":
    # Direct demonstration
    test_cases = ['%', 'hello%20world', '/path with spaces', 'already%20escaped%20path']
    
    for test in test_cases:
        print(f"\nTesting: {repr(test)}")
        escaped1 = django.utils.encoding.escape_uri_path(test)
        escaped2 = django.utils.encoding.escape_uri_path(escaped1)
        escaped3 = django.utils.encoding.escape_uri_path(escaped2)
        
        print(f"  1st escape: {repr(escaped1)}")
        print(f"  2nd escape: {repr(escaped2)}")
        print(f"  3rd escape: {repr(escaped3)}")
        
        if escaped1 != escaped2:
            print("  ❌ NOT IDEMPOTENT - This is a bug!")