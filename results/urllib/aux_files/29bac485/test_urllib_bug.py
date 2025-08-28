import urllib.parse
from hypothesis import given, strategies as st, settings

# Bug: urlparse/urlunparse round-trip fails for certain whitespace in netloc
@given(st.sampled_from(['\n', '\r', '\t', '\r\n']))
@settings(max_examples=10)
def test_urlunparse_urlparse_round_trip_whitespace_netloc(char):
    """Test that urlunparse/urlparse preserves whitespace characters in netloc.
    
    This test demonstrates that certain whitespace characters in the netloc
    component are silently removed during parsing, breaking the round-trip property.
    """
    # Create URL components with whitespace in netloc
    original_components = ('http', char, '/path', '', '', '')
    
    # Unparse to create URL
    url = urllib.parse.urlunparse(original_components)
    
    # Parse the URL back
    parsed = urllib.parse.urlparse(url)
    
    # The netloc should be preserved
    assert parsed.netloc == char, f"netloc {repr(char)} was changed to {repr(parsed.netloc)}"
    
    # Full round-trip should preserve all components
    reconstructed_components = (
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        parsed.query,
        parsed.fragment
    )
    assert reconstructed_components == original_components


if __name__ == "__main__":
    test_urlunparse_urlparse_round_trip_whitespace_netloc()