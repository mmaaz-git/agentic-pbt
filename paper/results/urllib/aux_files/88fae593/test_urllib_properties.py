import urllib.parse
import math
from hypothesis import given, strategies as st, assume, settings
import pytest


@given(st.text())
def test_quote_unquote_round_trip(s):
    quoted = urllib.parse.quote(s, safe='')
    unquoted = urllib.parse.unquote(quoted)
    assert s == unquoted


@given(st.text())
def test_quote_plus_unquote_plus_round_trip(s):
    quoted = urllib.parse.quote_plus(s, safe='')
    unquoted = urllib.parse.unquote_plus(quoted)
    assert s == unquoted


@given(st.binary())
def test_quote_unquote_bytes_round_trip(data):
    quoted = urllib.parse.quote_from_bytes(data, safe=b'')
    unquoted = urllib.parse.unquote_to_bytes(quoted)
    assert data == unquoted


@given(st.text())
def test_urlparse_urlunparse_round_trip(url):
    assume('\x00' not in url)
    assume('\r' not in url)
    assume('\n' not in url)
    assume('\t' not in url)
    
    parsed = urllib.parse.urlparse(url)
    unparsed = urllib.parse.urlunparse(parsed)
    
    parsed2 = urllib.parse.urlparse(unparsed)
    assert parsed == parsed2


@given(st.text())
def test_urlsplit_urlunsplit_round_trip(url):
    assume('\x00' not in url)
    assume('\r' not in url)
    assume('\n' not in url)
    assume('\t' not in url)
    
    split = urllib.parse.urlsplit(url)
    unsplit = urllib.parse.urlunsplit(split)
    
    split2 = urllib.parse.urlsplit(unsplit)
    assert split == split2


@given(
    st.dictionaries(
        st.text(min_size=1),
        st.one_of(
            st.text(),
            st.lists(st.text(), min_size=1)
        ),
        min_size=0,
        max_size=10
    )
)
def test_urlencode_parse_qs_round_trip(d):
    for key in d:
        assume('\x00' not in key)
        if isinstance(d[key], str):
            assume('\x00' not in d[key])
        else:
            for v in d[key]:
                assume('\x00' not in v)
    
    encoded = urllib.parse.urlencode(d, doseq=True)
    decoded = urllib.parse.parse_qs(encoded)
    
    for key, value in d.items():
        if isinstance(value, str):
            assert key in decoded
            assert value in decoded[key]
        else:
            assert key in decoded
            for v in value:
                assert v in decoded[key]


@given(st.text(), st.text())
def test_urljoin_properties(base, url):
    assume('\x00' not in base and '\x00' not in url)
    assume('\r' not in base and '\r' not in url)
    assume('\n' not in base and '\n' not in url)
    assume('\t' not in base and '\t' not in url)
    
    result = urllib.parse.urljoin(base, url)
    
    if url.startswith(('http://', 'https://', 'ftp://', '//')):
        parsed_url = urllib.parse.urlparse(url)
        parsed_result = urllib.parse.urlparse(result)
        if parsed_url.scheme:
            assert parsed_result.scheme == parsed_url.scheme or (not parsed_url.scheme and parsed_result.scheme)


@given(st.text())
def test_quote_idempotent(s):
    quoted1 = urllib.parse.quote(s, safe='')
    quoted2 = urllib.parse.quote(quoted1, safe='%')
    assert quoted1 == quoted2


@given(st.text())
def test_unquote_idempotent(s):
    unquoted1 = urllib.parse.unquote(s)
    unquoted2 = urllib.parse.unquote(unquoted1)
    
    if '%' not in unquoted1 or all(
        not (c == '%' and i + 2 < len(unquoted1) and 
             unquoted1[i+1:i+3].isalnum() and len(unquoted1[i+1:i+3]) == 2)
        for i, c in enumerate(unquoted1)
    ):
        assert unquoted1 == unquoted2


@given(st.text(alphabet=st.characters(blacklist_categories=['Cs', 'Cc'], blacklist_characters='\x00')))
def test_quote_preserves_safe_chars(s):
    safe_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~'
    quoted = urllib.parse.quote(s, safe=safe_chars)
    
    for char in s:
        if char in safe_chars:
            assert char in quoted


@given(st.text())
def test_quote_never_produces_null_bytes(s):
    quoted = urllib.parse.quote(s)
    assert '\x00' not in quoted
    quoted_plus = urllib.parse.quote_plus(s)
    assert '\x00' not in quoted_plus


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1),
            st.text()
        ),
        min_size=0,
        max_size=10
    )
)
def test_parse_qsl_urlencode_round_trip(pairs):
    for key, value in pairs:
        assume('\x00' not in key and '\x00' not in value)
    
    encoded = urllib.parse.urlencode(pairs)
    decoded = urllib.parse.parse_qsl(encoded)
    
    assert len(pairs) == len(decoded)
    for (k1, v1), (k2, v2) in zip(pairs, decoded):
        assert k1 == k2
        assert v1 == v2


@given(st.text())
def test_urldefrag_properties(url):
    assume('\x00' not in url)
    assume('\r' not in url)
    assume('\n' not in url)
    assume('\t' not in url)
    
    defragged = urllib.parse.urldefrag(url)
    
    if '#' in url:
        assert '#' not in defragged.url or defragged.url.index('#') > url.index('#')
        combined = defragged.url
        if defragged.fragment:
            combined = defragged.url + '#' + defragged.fragment
        parsed_original = urllib.parse.urlparse(url)
        parsed_combined = urllib.parse.urlparse(combined)
        assert parsed_original.fragment == parsed_combined.fragment
    else:
        assert defragged.fragment == ''
        assert defragged.url == url


@given(st.text(), st.text())  
def test_quote_consistency_with_different_safe(s, safe):
    assume(all(ord(c) < 128 for c in safe))
    
    quoted1 = urllib.parse.quote(s, safe=safe)
    quoted2 = urllib.parse.quote(s, safe=safe)
    assert quoted1 == quoted2


@given(st.dictionaries(st.text(), st.text(), min_size=0, max_size=20))
def test_parse_qs_preserve_keys(d):
    for k, v in d.items():
        assume('\x00' not in k and '\x00' not in v)
        assume('&' not in k and '=' not in k)
        assume('&' not in v and '=' not in v)
    
    encoded = urllib.parse.urlencode(d)
    decoded = urllib.parse.parse_qs(encoded)
    
    assert set(d.keys()) == set(decoded.keys())


@given(st.text())
def test_quote_length_increases_or_same(s):
    quoted = urllib.parse.quote(s)
    assert len(quoted) >= len(s)


@given(st.text())
def test_unquote_length_decreases_or_same(s):
    unquoted = urllib.parse.unquote(s)
    assert len(unquoted) <= len(s)


url_strategy = st.text().filter(
    lambda x: not any(c in x for c in '\x00\r\n\t')
)

@given(url_strategy, url_strategy)
def test_urljoin_absolute_url_overrides_base(base, absolute):
    assume(absolute.startswith(('http://', 'https://', 'ftp://', 'file://')))
    
    result = urllib.parse.urljoin(base, absolute)
    parsed_absolute = urllib.parse.urlparse(absolute)
    parsed_result = urllib.parse.urlparse(result)
    
    assert parsed_result.scheme == parsed_absolute.scheme
    assert parsed_result.netloc == parsed_absolute.netloc
    assert parsed_result.path == parsed_absolute.path


@given(st.binary())
def test_quote_from_bytes_returns_ascii(data):
    result = urllib.parse.quote_from_bytes(data)
    assert all(ord(c) < 128 for c in result)


@given(st.text())
def test_unquote_to_bytes_returns_bytes(s):
    result = urllib.parse.unquote_to_bytes(s)
    assert isinstance(result, bytes)