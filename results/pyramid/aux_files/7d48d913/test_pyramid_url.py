import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from pyramid.url import _join_elements, parse_url_overrides
from pyramid.encode import urlencode, url_quote
from pyramid.traversal import quote_path_segment, PATH_SEGMENT_SAFE
from urllib.parse import unquote


# Test 1: _join_elements round-trip property
# The function joins path elements with URL quoting, we should be able to recover them
@given(st.lists(st.text(min_size=1).filter(lambda x: '/' not in x), min_size=1, max_size=10))
def test_join_elements_round_trip(elements):
    """Test that joined elements can be split back to recover original elements"""
    # Join the elements
    joined = _join_elements(elements)
    
    # Split them back
    if joined:
        parts = joined.split('/')
        # Unquote each part
        decoded_parts = [unquote(part) for part in parts]
        
        # They should match the original elements
        assert decoded_parts == elements, f"Failed roundtrip: {elements} -> {joined} -> {decoded_parts}"


# Test 2: parse_url_overrides handles query parameters correctly
@given(
    query_dict=st.dictionaries(
        st.text(min_size=1, alphabet=st.characters(blacklist_characters='&=?#')),
        st.text(min_size=0, alphabet=st.characters(blacklist_characters='&=?#')),
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


# Test 3: parse_url_overrides handles None/empty anchor and query
@given(
    anchor=st.one_of(st.none(), st.just(''), st.text(min_size=1)),
    query=st.one_of(st.none(), st.just(''), st.text(min_size=1))
)  
def test_parse_url_overrides_empty_values(anchor, query):
    """Test that falsey anchor/query values are not included per documentation"""
    class MockRequest:
        def __init__(self):
            self.application_url = "http://example.com"
    
    request = MockRequest()
    kw = {}
    if anchor is not None:
        kw['_anchor'] = anchor
    if query is not None:
        kw['_query'] = query
    
    app_url, qs, frag = parse_url_overrides(request, kw)
    
    # Per documentation (line 241-242), falsey values should not be included
    if not anchor:
        assert frag == ''
    else:
        assert frag.startswith('#')
    
    if not query:
        assert qs == ''
    else:
        assert qs.startswith('?')


# Test 4: urlencode handles None values correctly  
@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, alphabet=st.characters(blacklist_characters='&=?#')),
            st.one_of(
                st.none(),
                st.text(alphabet=st.characters(blacklist_characters='&=?#')),
                st.lists(st.text(alphabet=st.characters(blacklist_characters='&=?#')), min_size=0, max_size=3)
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
            # Per documentation (line 50-51), None values should result in key= with no value
            assert f"{url_quote(key, '')}=" in result or result == f"{url_quote(key, '')}="
            # Should NOT have key=None
            assert f"{url_quote(key, '')}=None" not in result
        elif isinstance(value, list):
            # Lists should be expanded
            for v in value:
                encoded_key = url_quote(key, '')
                encoded_val = url_quote(v, '') if v else ''
                assert f"{encoded_key}={encoded_val}" in result or result == f"{encoded_key}={encoded_val}"


# Test 5: quote_path_segment idempotence for safe characters
@given(st.text(alphabet=PATH_SEGMENT_SAFE, min_size=1))
def test_quote_path_segment_safe_chars_unchanged(text):
    """Test that safe characters are not encoded by quote_path_segment"""
    quoted = quote_path_segment(text)
    # Safe characters should pass through unchanged
    assert quoted == text
    # Quoting again should not change it
    assert quote_path_segment(quoted) == quoted


# Test 6: _partial_application_url port handling for http/https
class TestPartialApplicationUrl:
    """Test the _partial_application_url method from URLMethodsMixin"""
    
    @given(
        scheme=st.sampled_from(['http', 'https']),
        host=st.text(min_size=1, alphabet=st.characters(whitelist_categories=['L', 'N'], whitelist_characters='.-')),
        port=st.one_of(st.none(), st.integers(min_value=1, max_value=65535).map(str))
    )
    def test_partial_application_url_default_ports(self, scheme, host, port):
        """Test that default ports are handled correctly for http/https"""
        # Create a mock request with the URLMethodsMixin behavior
        from pyramid.url import URLMethodsMixin
        
        class MockRequest(URLMethodsMixin):
            def __init__(self):
                self.environ = {
                    'wsgi.url_scheme': 'http',
                    'SERVER_NAME': 'localhost',
                    'SERVER_PORT': '80',
                    'HTTP_HOST': 'localhost:80'
                }
                self.script_name = ''
                self.url_encoding = 'utf-8'
        
        request = MockRequest()
        url = request._partial_application_url(scheme=scheme, host=host, port=port)
        
        # Check the URL structure
        assert url.startswith(f"{scheme}://")
        assert host in url
        
        # Check port handling per the documentation
        if scheme == 'https' and port == '443':
            # Port 443 should be omitted for https (line 99-100)
            assert ':443' not in url
        elif scheme == 'http' and port == '80':
            # Port 80 should be omitted for http (line 102-103)
            assert ':80' not in url
        elif port is not None and port not in ['80', '443']:
            # Other ports should be included
            assert f":{port}" in url


# Test 7: _join_elements handles special characters
@given(
    st.lists(
        st.text(alphabet=st.characters(blacklist_characters='/', min_codepoint=32), min_size=1),
        min_size=1,
        max_size=5
    )
)
def test_join_elements_special_chars(elements):
    """Test that _join_elements properly quotes special characters"""
    joined = _join_elements(elements)
    
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