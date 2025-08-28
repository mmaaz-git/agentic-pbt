import urllib.parse
from hypothesis import given, strategies as st, assume, settings, HealthCheck


@given(st.dictionaries(st.text(min_size=1), st.text(), min_size=0, max_size=10))
def test_urlencode_parse_qs_data_loss(d):
    """Test that urlencode -> parse_qs loses data with empty values."""
    for key in d:
        assume('\x00' not in key)
        assume('\x00' not in d[key])
    
    encoded = urllib.parse.urlencode(d)
    decoded = urllib.parse.parse_qs(encoded)  # default keep_blank_values=False
    
    # Check if any keys with empty values were lost
    for key, value in d.items():
        if value == '':
            # Empty values are lost by default
            assert key not in decoded
        else:
            assert key in decoded
            assert value in decoded[key]


@given(st.lists(st.tuples(st.text(min_size=1), st.text()), min_size=0, max_size=10))
def test_parse_qsl_data_loss(pairs):
    """Test that urlencode -> parse_qsl loses data with empty values."""
    for key, value in pairs:
        assume('\x00' not in key and '\x00' not in value)
    
    encoded = urllib.parse.urlencode(pairs)
    decoded = urllib.parse.parse_qsl(encoded)  # default keep_blank_values=False
    
    # Count non-empty values
    non_empty_pairs = [(k, v) for k, v in pairs if v != '']
    assert len(decoded) == len(non_empty_pairs)


@given(st.text(), st.text())
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_urljoin_absolute_url_property(base, absolute):
    """Test urljoin with absolute URLs."""
    assume('\x00' not in base and '\x00' not in absolute)
    assume('\r' not in base and '\r' not in absolute)
    assume('\n' not in base and '\n' not in absolute)
    assume('\t' not in base and '\t' not in absolute)
    
    # Only test with actual absolute URLs
    assume(absolute.startswith(('http://', 'https://', 'ftp://', 'file://')))
    
    result = urllib.parse.urljoin(base, absolute)
    
    # When joining with an absolute URL, the base should be ignored
    # and the result should match the absolute URL
    parsed_absolute = urllib.parse.urlparse(absolute)
    parsed_result = urllib.parse.urlparse(result)
    
    # The scheme, netloc, and path should match
    assert parsed_result.scheme == parsed_absolute.scheme
    assert parsed_result.netloc == parsed_absolute.netloc
    assert parsed_result.path == parsed_absolute.path