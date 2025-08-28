import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from pyramid.url import _join_elements, parse_url_overrides
from pyramid.encode import urlencode, url_quote
from pyramid.traversal import quote_path_segment, PATH_SEGMENT_SAFE
from urllib.parse import unquote


# Test 1: _join_elements round-trip property (fixed to use tuples)
@given(st.lists(st.text(min_size=1).filter(lambda x: '/' not in x and not any(0xD800 <= ord(c) <= 0xDFFF for c in x)), min_size=1, max_size=10))
def test_join_elements_round_trip(elements):
    """Test that joined elements can be split back to recover original elements"""
    # Convert to tuple since _join_elements uses @lru_cache
    elements_tuple = tuple(elements)
    
    # Join the elements
    joined = _join_elements(elements_tuple)
    
    # Split them back
    if joined:
        parts = joined.split('/')
        # Unquote each part
        decoded_parts = [unquote(part) for part in parts]
        
        # They should match the original elements
        assert decoded_parts == list(elements_tuple), f"Failed roundtrip: {elements_tuple} -> {joined} -> {decoded_parts}"


# Test 2: parse_url_overrides handles query parameters correctly (exclude surrogates)
@given(
    query_dict=st.dictionaries(
        st.text(min_size=1, alphabet=st.characters(blacklist_characters='&=?#', blacklist_categories=['Cs'])),
        st.text(min_size=0, alphabet=st.characters(blacklist_characters='&=?#', blacklist_categories=['Cs'])),
        min_size=0,
        max_size=5
    )
)
def test_parse_url_overrides_query_dict(query_dict):
    """Test that parse_url_overrides correctly encodes query dictionaries"""
    # Create a minimal mock request object
    class MockRequest:
        def __init__(self):
            self.application_url = "http://example.com"
    
    request = MockRequest()
    kw = {'_query': query_dict}
    
    app_url, qs, anchor = parse_url_overrides(request, kw)
    
    # If query_dict is empty, qs should be empty
    if not query_dict:
        assert qs == ''
    else:
        # Otherwise it should start with '?'
        assert qs.startswith('?')
        # The query string should contain encoded key-value pairs
        query_part = qs[1:]  # Remove the '?'
        # Should be valid URL encoding
        assert '&' in query_part or '=' in query_part or len(query_dict) == 1


# Test 3: urlencode handles None values correctly (exclude surrogates)
@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, alphabet=st.characters(blacklist_characters='&=?#', blacklist_categories=['Cs'])),
            st.one_of(
                st.none(),
                st.text(alphabet=st.characters(blacklist_characters='&=?#', blacklist_categories=['Cs'])),
                st.lists(st.text(alphabet=st.characters(blacklist_characters='&=?#', blacklist_categories=['Cs'])), min_size=0, max_size=3)
            )
        ),
        min_size=0,
        max_size=5
    )
)
def test_urlencode_none_values(query_list):
    """Test that urlencode handles None values as documented"""
    result = urlencode(query_list)
    
    for key, value in query_list:
        if value is None:
            # Per documentation, None values should result in key= with no value
            encoded_key = url_quote(key, '')
            # Should have key= somewhere
            assert f"{encoded_key}=" in result or result == f"{encoded_key}="
            # Should NOT have key=None
            assert f"{encoded_key}=None" not in result


# Test 4: Test urlencode with empty values
@given(
    query_list=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=10, alphabet=st.characters(blacklist_categories=['Cs'])),
            st.just('')
        ),
        min_size=1,
        max_size=3
    )
)
def test_urlencode_empty_values(query_list):
    """Test that urlencode handles empty string values correctly"""
    result = urlencode(query_list)
    
    # Empty values should produce key= with nothing after
    for key, value in query_list:
        encoded_key = url_quote(key, '')
        assert f"{encoded_key}=" in result


# Test 5: URL generation with special characters in elements
@given(
    elements=st.lists(
        st.text(min_size=1, alphabet=st.characters(blacklist_characters='/', blacklist_categories=['Cs'])),
        min_size=1,
        max_size=5
    )
)
def test_join_elements_special_chars(elements):
    """Test that _join_elements properly quotes special characters"""
    elements_tuple = tuple(elements)
    joined = _join_elements(elements_tuple)
    
    # Should not have unquoted special characters that would break URL structure
    # Slashes between elements are intentional separators
    parts = joined.split('/')
    assert len(parts) == len(elements)
    
    # Each part should be properly quoted
    for original, quoted_part in zip(elements, parts):
        # Unquoting should recover the original
        unquoted = unquote(quoted_part)
        assert unquoted == original


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])