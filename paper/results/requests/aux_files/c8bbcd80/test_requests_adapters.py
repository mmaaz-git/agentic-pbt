"""
Property-based tests for requests.adapters module
"""
import math
from urllib.parse import urlparse, quote

from hypothesis import assume, given, strategies as st
import pytest

from requests.adapters import (
    urldefragauth, 
    get_auth_from_url,
    select_proxy,
    HTTPAdapter
)


# Strategy for generating URLs with various components
@st.composite
def urls(draw):
    """Generate URLs with various components for testing."""
    scheme = draw(st.sampled_from(['http', 'https', 'ftp', 'file']))
    host = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_characters='/@#?:[]')))
    port = draw(st.one_of(st.none(), st.integers(min_value=1, max_value=65535)))
    path = draw(st.text(max_size=50, alphabet=st.characters(blacklist_characters='#?')))
    fragment = draw(st.text(max_size=20))
    
    if port:
        netloc = f"{host}:{port}"
    else:
        netloc = host
    
    url = f"{scheme}://{netloc}/{path}"
    if fragment:
        url = f"{url}#{fragment}"
    
    return url


@st.composite
def urls_with_auth(draw):
    """Generate URLs that may contain authentication."""
    scheme = draw(st.sampled_from(['http', 'https']))
    username = draw(st.text(max_size=20, alphabet=st.characters(blacklist_characters='/@:[]')))
    password = draw(st.text(max_size=20, alphabet=st.characters(blacklist_characters='/@:[]')))
    host = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_characters='/@#?:[]')))
    port = draw(st.one_of(st.none(), st.integers(min_value=1, max_value=65535)))
    path = draw(st.text(max_size=50, alphabet=st.characters(blacklist_characters='#?')))
    
    if username:
        if password:
            auth = f"{username}:{password}@"
        else:
            auth = f"{username}@"
    else:
        auth = ""
    
    if port:
        netloc = f"{auth}{host}:{port}"
    else:
        netloc = f"{auth}{host}"
    
    url = f"{scheme}://{netloc}/{path}"
    return url


# Test 1: urldefragauth idempotence property
@given(urls())
def test_urldefragauth_idempotence(url):
    """
    Property: urldefragauth should be idempotent - calling it twice 
    should give the same result as calling it once.
    """
    result_once = urldefragauth(url)
    result_twice = urldefragauth(result_once)
    assert result_once == result_twice


# Test 2: urldefragauth removes fragments
@given(urls())
def test_urldefragauth_removes_fragment(url):
    """
    Property: urldefragauth should remove the fragment from URLs.
    The result should never contain '#'.
    """
    result = urldefragauth(url)
    assert '#' not in result


# Test 3: urldefragauth removes authentication
@given(urls_with_auth())
def test_urldefragauth_removes_auth(url):
    """
    Property: urldefragauth should remove authentication from URLs.
    The netloc part should not contain '@' after processing.
    """
    result = urldefragauth(url)
    parsed = urlparse(result)
    # Check that there's no @ in the netloc (which would indicate auth)
    assert '@' not in parsed.netloc


# Test 4: get_auth_from_url always returns tuple of two strings
@given(st.text())
def test_get_auth_from_url_return_type(url):
    """
    Property: get_auth_from_url should always return a tuple of two strings,
    regardless of input.
    """
    result = get_auth_from_url(url)
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], str)
    assert isinstance(result[1], str)


# Test 5: get_auth_from_url returns empty strings for URLs without auth
@given(st.one_of(
    st.just("http://example.com"),
    st.just("https://www.google.com/search"),
    st.text(min_size=1).filter(lambda x: '@' not in x)
))
def test_get_auth_from_url_no_auth(url):
    """
    Property: URLs without authentication should return ("", "").
    """
    username, password = get_auth_from_url(url)
    if '@' not in url:
        assert username == ""
        assert password == ""


# Test 6: select_proxy returns None or value from proxies dict
@given(
    st.text(min_size=1),
    st.dictionaries(
        keys=st.sampled_from(['http', 'https', 'all', 'http://example.com', 'all://example.com']),
        values=st.text(min_size=1),
        min_size=0,
        max_size=5
    )
)
def test_select_proxy_returns_from_dict_or_none(url, proxies):
    """
    Property: select_proxy should return None or a value from the proxies dictionary.
    """
    result = select_proxy(url, proxies)
    if result is not None:
        assert result in proxies.values()


# Test 7: proxy_headers always returns a dictionary
@given(st.text())
def test_proxy_headers_returns_dict(proxy_url):
    """
    Property: HTTPAdapter.proxy_headers should always return a dictionary.
    """
    adapter = HTTPAdapter()
    result = adapter.proxy_headers(proxy_url)
    assert isinstance(result, dict)


# Test 8: proxy_headers includes auth header only when username present
@given(urls_with_auth())
def test_proxy_headers_auth_header_presence(proxy_url):
    """
    Property: proxy_headers should include Proxy-Authorization header
    if and only if the proxy URL contains a username.
    """
    adapter = HTTPAdapter()
    headers = adapter.proxy_headers(proxy_url)
    
    username, password = get_auth_from_url(proxy_url)
    
    if username:
        assert "Proxy-Authorization" in headers
    else:
        assert "Proxy-Authorization" not in headers


# Test 9: Round-trip property for URL with auth components
@given(
    st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_characters='/@:[]')),
    st.text(min_size=0, max_size=20, alphabet=st.characters(blacklist_characters='/@:[]'))
)
def test_auth_extraction_from_constructed_url(username, password):
    """
    Property: If we construct a URL with known auth components,
    get_auth_from_url should extract them correctly (accounting for URL encoding).
    """
    # Construct URL with auth
    if password:
        url = f"http://{quote(username, safe='')}:{quote(password, safe='')}@example.com/path"
    else:
        url = f"http://{quote(username, safe='')}@example.com/path"
    
    extracted_user, extracted_pass = get_auth_from_url(url)
    
    # The function should unquote the values
    assert extracted_user == username
    if password:
        assert extracted_pass == password
    else:
        assert extracted_pass == ""


# Test 10: select_proxy priority order
@given(st.sampled_from(['http', 'https']))
def test_select_proxy_priority(scheme):
    """
    Property: select_proxy should follow the documented priority order:
    scheme://hostname > scheme > all://hostname > all
    """
    hostname = "example.com"
    url = f"{scheme}://{hostname}/path"
    
    # Test that more specific proxy wins
    proxies = {
        f"{scheme}://{hostname}": "specific_proxy",
        scheme: "scheme_proxy",
        f"all://{hostname}": "all_host_proxy",
        "all": "all_proxy"
    }
    
    result = select_proxy(url, proxies)
    assert result == "specific_proxy"
    
    # Remove the most specific and test again
    del proxies[f"{scheme}://{hostname}"]
    result = select_proxy(url, proxies)
    assert result == "scheme_proxy"
    
    # Remove scheme-specific and test again
    del proxies[scheme]
    result = select_proxy(url, proxies)
    assert result == "all_host_proxy"
    
    # Remove all://hostname and test again
    del proxies[f"all://{hostname}"]
    result = select_proxy(url, proxies)
    assert result == "all_proxy"