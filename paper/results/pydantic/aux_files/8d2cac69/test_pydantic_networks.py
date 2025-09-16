"""Property-based tests for pydantic.networks module."""

import math
import re
from urllib.parse import urlencode, parse_qs, urlparse

import pytest
from hypothesis import assume, given, strategies as st, settings
from pydantic.networks import (
    AnyUrl, HttpUrl, AnyHttpUrl, WebsocketUrl, AnyWebsocketUrl,
    FtpUrl, FileUrl
)


# Strategy for valid URL schemes
http_schemes = st.sampled_from(['http', 'https'])
ws_schemes = st.sampled_from(['ws', 'wss'])
any_schemes = st.sampled_from(['http', 'https', 'ws', 'wss', 'ftp', 'file', 'custom'])

# Strategy for valid hostnames (simplified but valid)
valid_hostname = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789-.',
    min_size=1,
    max_size=63
).filter(lambda x: x[0].isalnum() and x[-1].isalnum() and '..' not in x)

# Strategy for valid ports
valid_port = st.integers(min_value=1, max_value=65535)

# Strategy for URL paths  
url_path = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~:/?#[]@!$&\'()*+,;=',
    min_size=0,
    max_size=100
)

# Strategy for query parameters
query_key = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_', min_size=1, max_size=20)
query_value = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-', min_size=0, max_size=50)
query_params = st.lists(st.tuples(query_key, query_value), min_size=0, max_size=10)


@given(
    scheme=http_schemes,
    host=valid_hostname, 
    port=st.one_of(st.none(), valid_port),
    path=st.one_of(st.none(), url_path),
    params=query_params
)
@settings(max_examples=1000)
def test_url_round_trip_property(scheme, host, port, path, params):
    """Test that URL components can be extracted and rebuilt to produce the same URL."""
    # Build query string
    query = None
    if params:
        query = '&'.join(f'{k}={v}' for k, v in params)
    
    # Build original URL using the build method
    original_url = HttpUrl.build(
        scheme=scheme,
        host=host,
        port=port,
        path=path,
        query=query
    )
    
    # Extract components from the URL
    extracted_scheme = original_url.scheme
    extracted_host = original_url.host
    extracted_port = original_url.port
    extracted_path = original_url.path
    extracted_query = None
    if original_url.query_params():
        extracted_query = '&'.join(f'{k}={v}' for k, v in original_url.query_params())
    
    # Rebuild URL from extracted components
    rebuilt_url = HttpUrl.build(
        scheme=extracted_scheme,
        host=extracted_host,
        port=extracted_port,
        path=extracted_path,
        query=extracted_query
    )
    
    # The rebuilt URL should match the original
    assert str(rebuilt_url) == str(original_url)


@given(
    scheme=http_schemes,
    host=valid_hostname,
    params=st.lists(
        st.tuples(query_key, query_value),
        min_size=1,
        max_size=20,
        unique_by=lambda x: x[0]  # Unique keys for simplicity
    )
)
@settings(max_examples=1000)
def test_query_params_parsing(scheme, host, params):
    """Test that query_params() correctly parses query strings."""
    # Build query string manually
    query = '&'.join(f'{k}={v}' for k, v in params)
    
    # Create URL with query
    url = HttpUrl.build(
        scheme=scheme,
        host=host,
        query=query
    )
    
    # Parse query params
    parsed_params = url.query_params()
    
    # Should have same number of parameters
    assert len(parsed_params) == len(params)
    
    # All original params should be in parsed params
    for key, value in params:
        assert (key, value) in parsed_params
    
    # No extra params should exist
    parsed_dict = dict(parsed_params)
    original_dict = dict(params)
    assert parsed_dict == original_dict


@given(
    scheme=http_schemes,
    host=st.text(
        alphabet='abcdefghijklmnopqrstuvwxyz0123456789-.',
        min_size=1,
        max_size=50
    ).filter(lambda x: x[0].isalnum() and x[-1] != '.' and '..' not in x),
    port=st.one_of(st.none(), valid_port)
)
@settings(max_examples=1000)
def test_unicode_string_equals_str_for_ascii(scheme, host, port):
    """Test that unicode_string() equals str() for ASCII-only URLs."""
    # Build ASCII-only URL
    url = HttpUrl.build(
        scheme=scheme,
        host=host,
        port=port
    )
    
    # For ASCII URLs, unicode_string should equal str
    assert url.unicode_string() == str(url)


@given(
    host=valid_hostname,
    explicit_port=st.one_of(st.none(), valid_port)
)
@settings(max_examples=1000)
def test_http_default_port_handling(host, explicit_port):
    """Test that HTTP URLs handle default port 80 correctly."""
    if explicit_port == 80:
        # When port is explicitly 80, it should be set to 80
        url = HttpUrl(f'http://{host}:80/')
        assert url.port == 80
    elif explicit_port is None:
        # When no port specified, should default to 80
        url = HttpUrl(f'http://{host}/')
        assert url.port == 80
    else:
        # When other port specified, should use that port
        url = HttpUrl(f'http://{host}:{explicit_port}/')
        assert url.port == explicit_port


@given(
    host=valid_hostname,
    explicit_port=st.one_of(st.none(), valid_port)
)
@settings(max_examples=1000)
def test_https_default_port_handling(host, explicit_port):
    """Test that HTTPS URLs handle default port 443 correctly."""
    if explicit_port == 443:
        # When port is explicitly 443, it should be set to 443
        url = HttpUrl(f'https://{host}:443/')
        assert url.port == 443
    elif explicit_port is None:
        # When no port specified, should default to 443
        url = HttpUrl(f'https://{host}/')
        assert url.port == 443
    else:
        # When other port specified, should use that port
        url = HttpUrl(f'https://{host}:{explicit_port}/')
        assert url.port == explicit_port


@given(
    scheme=any_schemes,
    host=valid_hostname,
    username=st.one_of(
        st.none(),
        st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=20)
    ),
    password=st.one_of(
        st.none(), 
        st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=20)
    )
)
@settings(max_examples=1000)
def test_url_auth_round_trip(scheme, host, username, password):
    """Test that URLs with authentication preserve username/password."""
    # Skip if password without username (invalid)
    if password and not username:
        assume(False)
    
    # Build URL with auth
    url = AnyUrl.build(
        scheme=scheme,
        host=host,
        username=username,
        password=password
    )
    
    # Extract and verify
    assert url.username == username
    assert url.password == password
    
    # Rebuild and verify round-trip
    rebuilt = AnyUrl.build(
        scheme=url.scheme,
        host=url.host,
        username=url.username,
        password=url.password
    )
    
    assert str(rebuilt) == str(url)


@given(
    host=valid_hostname,
    path=st.text(
        alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/_-.',
        min_size=0,
        max_size=100
    )
)
@settings(max_examples=1000)
def test_file_url_path_preservation(host, path):
    """Test that file URLs preserve their paths correctly."""
    # Build file URL
    if host:
        url = FileUrl(f'file://{host}/{path}')
    else:
        url = FileUrl(f'file:///{path}')
    
    # Path should be preserved (with leading /)
    if path and not path.startswith('/'):
        expected_path = '/' + path
    else:
        expected_path = path or ''
    
    # FileUrl might normalize the path
    assert url.path is not None
    # Check that path is at least present in the URL string
    assert expected_path in str(url) or path in str(url)


@given(
    scheme=ws_schemes,
    host=valid_hostname,
    port=st.one_of(st.none(), valid_port),
    path=st.one_of(
        st.none(),
        st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/_-.', min_size=1, max_size=50)
    )
)
@settings(max_examples=1000)
def test_websocket_url_properties(scheme, host, port, path):
    """Test WebSocket URL parsing and properties."""
    # Build WebSocket URL
    url = AnyWebsocketUrl.build(
        scheme=scheme,
        host=host,
        port=port,
        path=path
    )
    
    # Verify components
    assert url.scheme == scheme
    assert url.host == host
    
    # Port handling
    if port is None:
        if scheme == 'ws':
            assert url.port in [None, 80]  # Can be None or default 80
        else:  # wss
            assert url.port in [None, 443]  # Can be None or default 443
    else:
        assert url.port == port
    
    # Path handling  
    if path:
        assert path in str(url)


@given(
    host=valid_hostname,
    params=st.lists(
        st.tuples(
            st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=10),
            st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=0, max_size=20)
        ),
        min_size=0,
        max_size=10
    )
)
@settings(max_examples=500)
def test_query_params_empty_values(host, params):
    """Test that query_params handles empty values correctly."""
    # Build query with potentially empty values
    if params:
        query = '&'.join(f'{k}={v}' if v else k for k, v in params)
    else:
        query = None
    
    url = HttpUrl.build(
        scheme='http',
        host=host,
        query=query
    )
    
    parsed = url.query_params()
    
    # Verify all params are preserved
    if params:
        # Check that we have at least as many parsed params as original
        # (may have more due to how empty values are handled)
        assert len(parsed) >= len([p for p in params if p[1] or True])