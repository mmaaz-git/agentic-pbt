import urllib.request
from hypothesis import given, strategies as st, assume, settings
import string
import re


# Test 1: Round-trip property for pathname2url and url2pathname
@given(st.text(min_size=1, max_size=100))
def test_pathname_url_roundtrip(path):
    # Filter out null bytes which aren't valid in paths
    assume('\x00' not in path)
    
    try:
        url = urllib.request.pathname2url(path)
        reconstructed = urllib.request.url2pathname(url)
        
        # The round-trip should preserve the path
        assert reconstructed == path, f"Round-trip failed: {repr(path)} -> {repr(url)} -> {repr(reconstructed)}"
    except Exception as e:
        # If it fails, that might be a bug
        print(f"Exception with path {repr(path)}: {e}")
        raise


# Test 2: parse_keqv_list should handle edge cases with quotes
@given(st.lists(st.text(min_size=1).filter(lambda x: '=' in x), min_size=1, max_size=10))
def test_parse_keqv_list_properties(items):
    try:
        result = urllib.request.parse_keqv_list(items)
        
        # Property 1: Result should be a dict
        assert isinstance(result, dict)
        
        # Property 2: Number of keys should be <= number of input items
        assert len(result) <= len(items)
        
        # Property 3: All keys should come from splitting the items
        for item in items:
            if '=' in item:
                key = item.split('=', 1)[0]
                # Key should be in result (unless duplicate)
                if items.count(item) == 1:
                    assert key in result or any(i.startswith(key + '=') and i != item for i in items)
    except Exception as e:
        print(f"Exception with items {items}: {e}")
        raise


# Test 3: parse_keqv_list with empty values and edge cases
@given(st.text(min_size=0, max_size=50))
def test_parse_keqv_empty_value(key):
    # Test empty value handling
    assume('=' not in key)
    assume(key != '')
    
    test_cases = [
        f'{key}=',  # Empty value
        f'{key}=""',  # Empty quoted value
    ]
    
    for case in test_cases:
        try:
            result = urllib.request.parse_keqv_list([case])
            assert key in result
            # Check that empty values are handled correctly
            if case.endswith('=""'):
                assert result[key] == '', f"Empty quoted value not handled: {case} -> {result}"
            elif case.endswith('='):
                # Empty unquoted value
                assert result[key] == '', f"Empty value not handled: {case} -> {result}"
        except IndexError as e:
            print(f"IndexError with case {repr(case)}: {e}")
            raise


# Test 4: parse_http_list quote handling
@given(st.text(min_size=0, max_size=100))
def test_parse_http_list_quotes(content):
    # Test that quoted content preserves internal commas
    quoted = f'"{content}"'
    
    try:
        result = urllib.request.parse_http_list(quoted)
        
        # Should return a list with one element
        assert isinstance(result, list)
        assert len(result) == 1
        
        # The quotes should be preserved in output
        assert result[0] == quoted
        
        # Test with comma-separated
        if ',' in content:
            # Quoted comma should not split
            assert len(result) == 1
    except Exception as e:
        print(f"Exception with content {repr(content)}: {e}")
        raise


# Test 5: parse_http_list escape handling  
@given(st.text(alphabet=string.printable, min_size=1, max_size=50))
def test_parse_http_list_escapes(text):
    # Test escape sequences in quoted strings
    assume('"' not in text and '\\' not in text)
    
    # Create escaped quote inside quoted string
    test_str = f'"{text}\\"escaped"'
    
    try:
        result = urllib.request.parse_http_list(test_str)
        assert len(result) == 1
        # Should preserve the escaped quote
        assert '\\"' in result[0] or '"escaped' in result[0]
    except Exception as e:
        print(f"Exception with test_str {repr(test_str)}: {e}")
        raise


# Test 6: Test parse_keqv_list with values that have no closing quote
@given(st.text(min_size=1, max_size=20).filter(lambda x: '=' not in x and '"' not in x))
def test_parse_keqv_unclosed_quote(key):
    # Test value with opening quote but no closing quote
    test_case = f'{key}="unclosed'
    
    try:
        result = urllib.request.parse_keqv_list([test_case])
        # This might cause issues with the slicing v[1:-1]
        assert key in result
    except IndexError as e:
        print(f"IndexError with unclosed quote: {repr(test_case)}")
        raise
    except Exception as e:
        print(f"Other exception with {repr(test_case)}: {e}")
        # This could be expected behavior


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])