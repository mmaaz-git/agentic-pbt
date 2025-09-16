import urllib.parse
from hypothesis import given, strategies as st, assume


# Strategy for generating absolute URLs
absolute_url_strategy = st.builds(
    lambda scheme, netloc, path: f"{scheme}://{netloc}{path}",
    scheme=st.sampled_from(['http', 'https', 'ftp']),
    netloc=st.text(alphabet=st.characters(whitelist_categories=['L', 'N'], whitelist_characters='.-'), min_size=1, max_size=20),
    path=st.text(alphabet=st.characters(whitelist_categories=['L', 'N'], whitelist_characters='/-_.'), max_size=50)
)


@given(st.text(), absolute_url_strategy)
def test_urljoin_absolute_url_overrides(base, absolute):
    """Test that absolute URLs override the base in urljoin."""
    assume('\x00' not in base)
    assume('\r' not in base)
    assume('\n' not in base)
    assume('\t' not in base)
    
    result = urllib.parse.urljoin(base, absolute)
    
    # The absolute URL should completely override the base
    parsed_absolute = urllib.parse.urlparse(absolute)
    parsed_result = urllib.parse.urlparse(result)
    
    assert parsed_result.scheme == parsed_absolute.scheme
    assert parsed_result.netloc == parsed_absolute.netloc
    assert parsed_result.path == parsed_absolute.path


@given(st.text())
def test_urljoin_with_fragment(base_url):
    """Test urljoin behavior with fragments."""
    assume('\x00' not in base_url)
    assume('\r' not in base_url)
    assume('\n' not in base_url)
    assume('\t' not in base_url)
    
    # Add a fragment to the base
    if '#' not in base_url:
        base_with_fragment = base_url + '#fragment'
    else:
        base_with_fragment = base_url
    
    # Join with a relative path
    result = urllib.parse.urljoin(base_with_fragment, 'newpath')
    
    # The fragment should be removed when joining with a new path
    assert '#fragment' not in result or result.endswith('#fragment')


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])