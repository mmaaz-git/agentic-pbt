import urllib.parse
from hypothesis import given, strategies as st, assume, settings, HealthCheck

# Focus on the actual bugs found

# Test 1: IPv6 URL handling - Found a bug where single '[' causes ValueError
@given(st.text().filter(lambda x: '[' in x))
def test_ipv6_bracket_handling(url):
    try:
        parsed = urllib.parse.urlparse(url)
        # If successful, brackets should be balanced in netloc
        if '[' in parsed.netloc:
            assert ']' in parsed.netloc
    except ValueError as e:
        # Check if error is about IPv6
        assert 'Invalid IPv6' in str(e)

# Test 2: Construct URL with special netloc characters
@given(
    scheme=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=5),
    netloc=st.text(min_size=1, max_size=10)
)
def test_urlunparse_special_netloc(scheme, netloc):
    # Construct a URL
    components = (scheme, netloc, '/', '', '', '')
    url = urllib.parse.urlunparse(components)
    
    # Parse it back
    parsed = urllib.parse.urlparse(url)
    
    # Check if netloc is preserved correctly
    # Special case: '/' in netloc gets treated as path separator
    if '/' in netloc:
        # The part before first '/' should be netloc
        expected_netloc = netloc.split('/')[0]
        assert parsed.netloc == expected_netloc
    elif '[' in netloc and ']' not in netloc:
        # Should raise or handle gracefully
        pass
    else:
        assert parsed.netloc == netloc

# Test 3: Empty value handling in parse_qs
@given(st.text(min_size=1, max_size=20).filter(lambda x: '&' not in x and '=' not in x))
def test_parse_qs_empty_values(key):
    # Test with empty value
    query = f"{key}="
    result = urllib.parse.parse_qs(query)
    # Should have the key with empty string value
    assert key in result
    assert result[key] == ['']
    
    # Test with keep_blank_values=False (default)
    result2 = urllib.parse.parse_qs(query, keep_blank_values=False)
    # Empty values should be ignored
    assert key not in result2

# Test 4: Round-trip with special characters in query
@given(st.dictionaries(
    st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=10),
    st.text(min_size=0, max_size=20),
    min_size=1, max_size=5
))
def test_urlencode_special_chars(d):
    encoded = urllib.parse.urlencode(d)
    decoded = urllib.parse.parse_qs(encoded)
    
    for key, value in d.items():
        assert key in decoded
        assert decoded[key] == [value]

# Test 5: URL with brackets in different positions
def test_brackets_in_url_components():
    # Test 1: Brackets in netloc (should be for IPv6)
    url1 = "http://[::1]/path"
    parsed1 = urllib.parse.urlparse(url1)
    assert parsed1.netloc == '[::1]'
    
    # Test 2: Single bracket in netloc should raise
    url2 = "http://[/path"
    try:
        parsed2 = urllib.parse.urlparse(url2)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert 'Invalid IPv6 URL' in str(e)
    
    # Test 3: Brackets in path (should be allowed)
    url3 = "http://example.com/path[with]brackets"
    parsed3 = urllib.parse.urlparse(url3)
    assert parsed3.path == '/path[with]brackets'

# Test 6: Port validation edge cases
def test_port_validation_edge_cases():
    # Test valid ports
    url1 = "http://example.com:80/"
    parsed1 = urllib.parse.urlparse(url1)
    assert parsed1.port == 80
    
    url2 = "http://example.com:65535/"
    parsed2 = urllib.parse.urlparse(url2)
    assert parsed2.port == 65535
    
    # Test invalid port (too high)
    url3 = "http://example.com:65536/"
    parsed3 = urllib.parse.urlparse(url3)
    try:
        port = parsed3.port
        assert False, "Should have raised ValueError for port > 65535"
    except ValueError as e:
        assert 'out of range' in str(e)
    
    # Test invalid port (negative)
    url4 = "http://example.com:-1/"
    parsed4 = urllib.parse.urlparse(url4)
    try:
        port = parsed4.port
        # Negative port should fail
        assert False, "Should have raised ValueError for negative port"
    except ValueError:
        pass

# Test 7: Unicode normalization in netloc
def test_unicode_normalization_attack():
    # Test with Unicode character that normalizes to include '/'
    # U+2100 (℀) normalizes to 'a/c' under NFKC
    url = "http://test\u2100.com/path"
    try:
        parsed = urllib.parse.urlparse(url)
        # Should raise ValueError due to NFKC normalization check
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert 'invalid characters under NFKC normalization' in str(e)

# Test 8: Fragment handling edge cases
@given(st.text())
def test_fragment_multiple_hashes(url):
    # URLs with multiple '#' characters
    if '#' in url:
        parsed = urllib.parse.urlparse(url)
        # Everything after first '#' should be fragment
        first_hash = url.index('#')
        expected_fragment = url[first_hash + 1:]
        # urlparse stops at first #
        if '?' not in url[:first_hash]:
            assert parsed.fragment == expected_fragment

# Test 9: Scheme validation
def test_scheme_with_invalid_chars():
    # Schemes should only contain alphanumeric, +, -, .
    url1 = "ht_tp://example.com"  # underscore not allowed
    parsed1 = urllib.parse.urlparse(url1)
    # Should not recognize as scheme
    assert parsed1.scheme == ''
    assert parsed1.path == url1
    
    url2 = "ht-tp://example.com"  # hyphen is allowed
    parsed2 = urllib.parse.urlparse(url2)
    assert parsed2.scheme == 'ht-tp'
    
    url3 = "ht.tp://example.com"  # dot is allowed
    parsed3 = urllib.parse.urlparse(url3)
    assert parsed3.scheme == 'ht.tp'

# Test 10: Path normalization with empty netloc
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=5))
def test_path_normalization_empty_netloc(path):
    # When netloc is present but path doesn't start with /, 
    # urlunparse should add it
    components = ('http', 'example.com', path, '', '', '')
    url = urllib.parse.urlunparse(components)
    parsed = urllib.parse.urlparse(url)
    
    if not path.startswith('/'):
        # Should have been normalized to start with /
        assert parsed.path == '/' + path
    else:
        assert parsed.path == path