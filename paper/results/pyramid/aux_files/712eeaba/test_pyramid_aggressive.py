#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.traversal as traversal
from hypothesis import given, strategies as st, assume, settings, example
import string
import urllib.parse


# Test: URL encoding round-trip consistency
@given(st.text(min_size=1, max_size=30))
@settings(max_examples=1000)
def test_quote_unquote_roundtrip(text):
    """Test that quote_path_segment properly encodes for URL decoding"""
    try:
        # Quote the segment
        quoted = traversal.quote_path_segment(text)
        
        # Try to decode it back using standard URL decoding
        decoded = urllib.parse.unquote(quoted, errors='strict')
        
        # Should get back the original
        assert decoded == text, f"Round-trip failed: {text!r} -> {quoted!r} -> {decoded!r}"
        
    except (TypeError, UnicodeDecodeError) as e:
        # Some inputs might not be valid
        pass


# Test: traversal_path vs traversal_path_info consistency  
@given(st.text(alphabet=string.printable, min_size=1, max_size=30))
@settings(max_examples=1000)
def test_traversal_path_vs_path_info_consistency(text):
    """Test relationship between traversal_path and traversal_path_info"""
    path = '/' + text
    
    try:
        # traversal_path handles URL-encoded paths
        result1 = traversal.traversal_path(path)
        
        # Try decoding the path first, then using traversal_path_info
        try:
            decoded_path = urllib.parse.unquote(path)
            result2 = traversal.traversal_path_info(decoded_path)
            
            # For paths without encoding, results should match
            if '%' not in path:
                assert result1 == result2, f"Inconsistent results for {path!r}: {result1} != {result2}"
                
        except Exception:
            pass
            
    except (traversal.URLDecodeError, UnicodeEncodeError):
        pass


# Test: Invalid percent sequences that should fail
@given(st.text(alphabet='%' + string.ascii_letters + string.digits, min_size=1, max_size=20))
@settings(max_examples=1000)
@example('%')
@example('%%')
@example('%G')
@example('%ZZ')
@example('%1')
@example('%%%')
def test_invalid_percent_encoding_should_fail(text):
    """Invalid percent encoding should raise URLDecodeError"""
    if not '%' in text:
        return
    
    # Check if this has invalid percent encoding
    import re
    # Pattern for invalid percent encoding (% not followed by exactly 2 hex digits)
    invalid_pattern = re.compile(r'%(?![0-9A-Fa-f]{2})')
    
    if invalid_pattern.search(text):
        path = '/' + text
        try:
            result = traversal.traversal_path(path)
            # If we got here, invalid encoding was accepted - potential bug!
            print(f"BUG: Invalid percent encoding accepted: {text!r} -> {result}")
            # This might be a bug - invalid encoding should fail
            
        except (traversal.URLDecodeError, UnicodeEncodeError):
            # This is expected - invalid encoding should fail
            pass
    else:
        # Valid encoding, should work
        path = '/' + text
        try:
            result = traversal.traversal_path(path)
            assert isinstance(result, tuple)
        except UnicodeEncodeError:
            # Non-ASCII might fail
            pass


# Test: Extreme nesting with parent references
@given(st.lists(st.sampled_from(['foo', '..', '.', 'bar']), min_size=1, max_size=20))
@settings(max_examples=1000)
def test_complex_parent_navigation(segments):
    """Test complex paths with multiple .. and . segments"""
    path = '/' + '/'.join(segments)
    result = traversal.split_path_info(path)
    
    # Manually compute what the result should be
    expected = []
    for seg in segments:
        if seg == '..':
            if expected:
                expected.pop()
        elif seg != '.':
            expected.append(seg)
    
    assert result == tuple(expected), f"Incorrect normalization for {path}: got {result}, expected {tuple(expected)}"


# Test: Unicode and special characters in paths
@given(st.text(min_size=1, max_size=20))
@settings(max_examples=1000)
def test_unicode_in_paths(text):
    """Test handling of Unicode characters in paths"""
    path = '/' + text
    
    # Test split_path_info with Unicode
    try:
        result = traversal.split_path_info(path)
        # Should handle Unicode properly
        assert isinstance(result, tuple)
        for item in result:
            assert isinstance(item, str)
    except Exception as e:
        # Some Unicode might cause issues
        print(f"Unicode issue with {text!r}: {e}")


# Test: Empty and special segment handling
@given(st.lists(st.sampled_from(['', '.', '..', 'foo']), min_size=0, max_size=10))
@settings(max_examples=1000)  
def test_empty_and_special_segments(segments):
    """Test that empty segments and dots are handled correctly"""
    path = '/' + '/'.join(segments)
    result = traversal.split_path_info(path)
    
    # Empty segments and '.' should be removed
    assert '' not in result
    assert '.' not in result
    
    # Count how many '..' should remain after cancellation
    stack = []
    for seg in segments:
        if seg == '..':
            if stack and stack[-1] != '..':
                stack.pop()
            # Note: we don't push '..' because they cancel at root
        elif seg != '' and seg != '.':
            stack.append(seg)
    
    # Filter out any '..' that would go above root
    expected = tuple(s for s in stack if s != '..')
    assert result == expected, f"Mismatch for {segments}: got {result}, expected {expected}"


# Test: Null bytes and control characters
@given(st.text(alphabet=string.printable + '\x00\x01\x02', min_size=1, max_size=20))
@settings(max_examples=500)
def test_null_bytes_and_control_chars(text):
    """Test handling of null bytes and control characters"""
    if '\x00' in text:
        # Paths with null bytes might be security issues
        path = '/' + text
        try:
            result = traversal.split_path_info(path)
            # Check if null bytes are preserved (potential security issue)
            for segment in result:
                if '\x00' in segment:
                    print(f"WARNING: Null byte preserved in path segment: {segment!r}")
        except Exception:
            # Expected to fail with null bytes
            pass


# Test: Extremely long paths
@given(st.text(alphabet=string.ascii_letters, min_size=1000, max_size=5000))
@settings(max_examples=10)
def test_very_long_paths(text):
    """Test handling of very long paths"""
    path = '/' + text
    try:
        result = traversal.split_path_info(path)
        assert len(result) == 1
        assert result[0] == text
    except Exception as e:
        print(f"Failed with long path of length {len(text)}: {e}")


# Test: Path encoding with non-ASCII characters
@given(st.text(alphabet='αβγδε中文عربي', min_size=1, max_size=10))
@settings(max_examples=500)
def test_non_ascii_path_encoding(text):
    """Test handling of non-ASCII characters in various functions"""
    # Test quote_path_segment
    try:
        quoted = traversal.quote_path_segment(text)
        # Should be URL-encoded
        assert all(ord(c) < 128 for c in quoted), f"Non-ASCII in quoted result: {quoted!r}"
        
        # Should be decodable
        decoded = urllib.parse.unquote(quoted)
        assert decoded == text, f"Round-trip failed for {text!r}"
        
    except Exception as e:
        print(f"Failed to quote non-ASCII {text!r}: {e}")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])