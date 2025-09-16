import math
import urllib.parse
from hypothesis import given, strategies as st, assume, settings

# Test 1: Round-trip property for quote/unquote
@given(st.text())
def test_quote_unquote_round_trip(s):
    quoted = urllib.parse.quote(s)
    unquoted = urllib.parse.unquote(quoted)
    assert unquoted == s

# Test 2: Round-trip property for quote_plus/unquote_plus
@given(st.text())
def test_quote_plus_unquote_plus_round_trip(s):
    quoted = urllib.parse.quote_plus(s)
    unquoted = urllib.parse.unquote_plus(quoted)
    assert unquoted == s

# Test 3: Round-trip property for quote_from_bytes/unquote_to_bytes
@given(st.binary())
def test_quote_bytes_round_trip(b):
    try:
        quoted = urllib.parse.quote_from_bytes(b)
        unquoted = urllib.parse.unquote_to_bytes(quoted)
        assert unquoted == b
    except UnicodeDecodeError:
        pass  # Some bytes can't be decoded

# Test 4: urlparse/urlunparse round-trip
@given(st.text(min_size=1).filter(lambda x: ':' in x or '//' in x))
def test_urlparse_urlunparse_round_trip(url):
    parsed = urllib.parse.urlparse(url)
    unparsed = urllib.parse.urlunparse(parsed)
    # Re-parse to normalize
    reparsed = urllib.parse.urlparse(unparsed)
    assert parsed == reparsed

# Test 5: urlsplit/urlunsplit round-trip
@given(st.text(min_size=1).filter(lambda x: ':' in x or '//' in x))
def test_urlsplit_urlunsplit_round_trip(url):
    split = urllib.parse.urlsplit(url)
    unsplit = urllib.parse.urlunsplit(split)
    # Re-split to normalize
    resplit = urllib.parse.urlsplit(unsplit)
    assert split == resplit

# Test 6: Port number invariant
@given(st.text())
def test_port_number_range(url):
    try:
        parsed = urllib.parse.urlparse(url)
        port = parsed.port
        if port is not None:
            assert 0 <= port <= 65535
    except (ValueError, AttributeError):
        pass  # Invalid URL or no port

# Test 7: urlencode/parse_qs round-trip for simple dicts
@given(st.dictionaries(
    st.text(min_size=1).filter(lambda x: '&' not in x and '=' not in x and '%' not in x),
    st.text().filter(lambda x: '&' not in x and '=' not in x and '%' not in x),
    min_size=1
))
def test_urlencode_parse_qs_round_trip(d):
    # Convert to list format expected by parse_qs
    encoded = urllib.parse.urlencode(d)
    decoded = urllib.parse.parse_qs(encoded)
    # parse_qs returns lists of values
    for key, value in d.items():
        assert key in decoded
        assert decoded[key] == [value]

# Test 8: parse_qsl preserves order
@given(st.lists(
    st.tuples(
        st.text(min_size=1).filter(lambda x: '&' not in x and '=' not in x and '%' not in x),
        st.text().filter(lambda x: '&' not in x and '=' not in x and '%' not in x)
    ),
    min_size=1
))
def test_parse_qsl_preserves_order(pairs):
    encoded = urllib.parse.urlencode(pairs)
    decoded = urllib.parse.parse_qsl(encoded)
    assert decoded == pairs

# Test 9: urldefrag round-trip
@given(st.text())
def test_urldefrag_round_trip(url):
    defragged, fragment = urllib.parse.urldefrag(url)
    if '#' in url:
        # If there was a fragment, reconstructing should give original
        reconstructed = defragged + '#' + fragment
        assert reconstructed == url
    else:
        # If no fragment, defragged should equal original
        assert defragged == url and fragment == ''

# Test 10: urljoin properties
@given(st.text(), st.text())
def test_urljoin_with_absolute_url(base, url):
    # If url is absolute (has scheme), result should be url
    if url and ':' in url and url.split(':')[0].replace('+', '').replace('-', '').replace('.', '').isalnum():
        result = urllib.parse.urljoin(base, url)
        # Check if url had a scheme
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.scheme:
            assert result == url

# Test 11: quote should be idempotent when applied twice
@given(st.text())
def test_quote_idempotent(s):
    once = urllib.parse.quote(s)
    twice = urllib.parse.quote(once)
    # After first quote, all special chars are encoded
    # So second quote should only encode the % signs
    assert urllib.parse.unquote(urllib.parse.unquote(twice)) == s

# Test 12: Empty string handling
def test_empty_string_handling():
    assert urllib.parse.quote('') == ''
    assert urllib.parse.unquote('') == ''
    assert urllib.parse.quote_plus('') == ''
    assert urllib.parse.unquote_plus('') == ''
    assert urllib.parse.urlencode({}) == ''
    assert urllib.parse.parse_qs('') == {}
    assert urllib.parse.parse_qsl('') == []

# Test 13: Special characters in safe parameter
@given(st.text(), st.text())
def test_quote_with_safe_param(s, safe):
    try:
        quoted = urllib.parse.quote(s, safe=safe)
        # Result should be a string
        assert isinstance(quoted, str)
        # Unquoting should work
        unquoted = urllib.parse.unquote(quoted)
        # Characters in safe should not be encoded (if ASCII)
        for char in safe:
            if ord(char) < 128 and char in s:
                # This char should appear unencoded in result
                pass  # Complex to verify due to encoding rules
    except (UnicodeEncodeError, TypeError):
        pass  # Some combinations are invalid

# Test 14: Bytes vs string consistency
@given(st.text())
def test_quote_bytes_string_consistency(s):
    try:
        # Quote as string
        quoted_str = urllib.parse.quote(s)
        # Quote as bytes
        quoted_bytes = urllib.parse.quote_from_bytes(s.encode('utf-8'))
        assert quoted_str == quoted_bytes
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass

# Test 15: Parse result attributes
@given(st.text(min_size=1).filter(lambda x: '//' in x))
def test_parse_result_attributes(url):
    try:
        parsed = urllib.parse.urlparse(url)
        # These should always exist (may be empty strings)
        assert hasattr(parsed, 'scheme')
        assert hasattr(parsed, 'netloc')
        assert hasattr(parsed, 'path')
        assert hasattr(parsed, 'params')
        assert hasattr(parsed, 'query')
        assert hasattr(parsed, 'fragment')
        # If netloc exists, might have username/password/hostname/port
        if parsed.netloc:
            assert hasattr(parsed, 'hostname')
            assert hasattr(parsed, 'port')
            assert hasattr(parsed, 'username')
            assert hasattr(parsed, 'password')
    except ValueError:
        pass  # Invalid URL

# Test 16: IPv6 URL handling
@given(st.text())
def test_ipv6_url_validation(s):
    # Test URLs with brackets
    if '[' in s or ']' in s:
        try:
            parsed = urllib.parse.urlparse(s)
            # If parsing succeeded with brackets, they should be balanced
            if '[' in parsed.netloc:
                assert ']' in parsed.netloc
            if ']' in parsed.netloc:
                assert '[' in parsed.netloc
        except ValueError as e:
            # Should raise for unbalanced brackets
            assert 'Invalid IPv6 URL' in str(e) or 'Invalid IPv6' in str(e)

# Test 17: Encoding parameter validation
@given(st.text(), st.sampled_from(['utf-8', 'ascii', 'latin-1', 'utf-16']))
def test_quote_encoding_parameter(s, encoding):
    try:
        quoted = urllib.parse.quote(s, encoding=encoding)
        unquoted = urllib.parse.unquote(quoted, encoding=encoding)
        assert unquoted == s
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass  # Some strings can't be encoded in all encodings

# Test 18: URL with all components
@given(
    scheme=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=10),
    netloc=st.text(min_size=1, max_size=20).filter(lambda x: '@' not in x and ':' not in x),
    path=st.text(max_size=20),
    params=st.text(max_size=10).filter(lambda x: ';' not in x),
    query=st.text(max_size=20).filter(lambda x: '?' not in x),
    fragment=st.text(max_size=10).filter(lambda x: '#' not in x)
)
def test_construct_and_parse_url(scheme, netloc, path, params, query, fragment):
    components = (scheme, netloc, path, params, query, fragment)
    url = urllib.parse.urlunparse(components)
    parsed = urllib.parse.urlparse(url)
    # The parsed result should match our input (with some normalization)
    assert parsed.scheme == scheme.lower()  # Schemes are lowercased
    assert parsed.netloc == netloc
    # Path normalization may occur
    if netloc and not path.startswith('/'):
        assert parsed.path == '/' + path
    else:
        assert parsed.path == path
    assert parsed.params == params
    assert parsed.query == query
    assert parsed.fragment == fragment

# Test 19: unquote with invalid percent encoding
@given(st.text())
def test_unquote_invalid_percent(s):
    # Add invalid percent sequences
    invalid = s + '%' + '%ZZ' + '%1' + '%%'
    try:
        result = urllib.parse.unquote(invalid)
        # Should not raise, but handle gracefully
        assert isinstance(result, str)
    except Exception as e:
        # Should not raise exceptions
        assert False, f"Unexpected exception: {e}"

# Test 20: Max fields protection in parse_qs
@given(st.integers(min_value=1, max_value=100), st.integers(min_value=1, max_value=200))
def test_parse_qs_max_fields(max_fields, num_fields):
    # Create query with num_fields
    query = '&'.join([f'field{i}=value{i}' for i in range(num_fields)])
    
    if num_fields > max_fields:
        # Should raise ValueError
        try:
            urllib.parse.parse_qs(query, max_num_fields=max_fields)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert 'Max number of fields exceeded' in str(e)
    else:
        # Should work fine
        result = urllib.parse.parse_qs(query, max_num_fields=max_fields)
        assert len(result) == num_fields