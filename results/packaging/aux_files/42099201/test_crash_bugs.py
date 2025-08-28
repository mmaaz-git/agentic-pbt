"""Hunt for crashes and serious parsing bugs"""

from hypothesis import given, strategies as st, settings, assume
from packaging.requirements import Requirement, InvalidRequirement
import string


# More aggressive fuzzing focused on finding crashes
@given(st.text(min_size=1, max_size=1000))
@settings(max_examples=5000, deadline=None)
def test_no_crashes_on_any_input(text):
    """Test that the parser never crashes, only raises InvalidRequirement"""
    try:
        req = Requirement(text)
        # If it parses, basic properties should exist
        assert req.name is not None
        assert req.extras is not None
        assert req.specifier is not None
        
        # String representation should not crash
        str_repr = str(req)
        assert isinstance(str_repr, str)
        
        # Should be able to parse its own output
        req2 = Requirement(str_repr)
        assert req2.name == req.name
        
    except InvalidRequirement:
        # This is the expected exception for invalid input
        pass
    except Exception as e:
        # Any other exception is a bug
        print(f"UNEXPECTED EXCEPTION: {type(e).__name__}: {e}")
        print(f"Input: {repr(text)}")
        raise


# Test for infinite loops or performance issues
@given(st.text(alphabet="[]", min_size=100, max_size=1000))
@settings(max_examples=100, deadline=None)
def test_nested_brackets_performance(brackets):
    """Test that deeply nested brackets don't cause performance issues"""
    req_str = f"package{brackets}"
    try:
        req = Requirement(req_str)
    except InvalidRequirement:
        pass


# Test Unicode handling
@given(st.text(alphabet=st.characters(min_codepoint=0x80, max_codepoint=0x10ffff), min_size=1, max_size=50))
def test_unicode_handling(unicode_text):
    """Test that Unicode is handled properly"""
    try:
        req = Requirement(unicode_text)
        # Should handle Unicode gracefully
        str(req)
    except InvalidRequirement:
        pass
    except UnicodeError as e:
        print(f"Unicode error with: {repr(unicode_text)}: {e}")
        raise


# Test null bytes and control characters
@given(st.text(alphabet="\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f", min_size=1, max_size=20))
def test_control_characters(control_chars):
    """Test handling of control characters"""
    req_str = f"package{control_chars}"
    try:
        req = Requirement(req_str)
    except InvalidRequirement:
        pass
    except Exception as e:
        print(f"Unexpected error with control chars {repr(control_chars)}: {e}")
        raise


# Test very long single tokens
@given(st.text(alphabet=string.ascii_letters, min_size=1000, max_size=10000))
@settings(max_examples=10)
def test_long_names(long_name):
    """Test handling of very long package names"""
    try:
        req = Requirement(long_name)
        assert req.name == long_name
        
        # Round-trip should work
        req2 = Requirement(str(req))
        assert req2.name == long_name
    except InvalidRequirement:
        pass


# Test recursive or self-referential patterns
@given(st.text())
def test_self_referential_patterns(text):
    """Test patterns that might cause issues in recursive parsing"""
    # Create potentially problematic patterns
    patterns = [
        f"{text}[{text}]",  # Self-referential extras
        f"{text}=={text}",  # Self-referential version
        f"{text};{text}",   # Self-referential marker
    ]
    
    for pattern in patterns:
        try:
            req = Requirement(pattern)
            # Should handle these gracefully
            str(req)
        except InvalidRequirement:
            pass
        except RecursionError as e:
            print(f"Recursion error with pattern {repr(pattern)}: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error with pattern {repr(pattern)}: {e}")
            raise


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])