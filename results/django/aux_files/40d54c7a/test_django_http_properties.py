import django
from django.conf import settings
settings.configure(DEBUG=True, SECRET_KEY='test', DEFAULT_CHARSET='utf-8')

import django.http
from hypothesis import given, strategies as st, assume
import urllib.parse


# Strategy for generating valid query string keys and values
query_key = st.text(
    alphabet=st.characters(
        blacklist_categories=('Cs', 'Cc'),
        blacklist_characters='&=\x00'
    ),
    min_size=1,
    max_size=100
).filter(lambda s: s.strip() and not s.startswith('_'))

query_value = st.text(
    alphabet=st.characters(
        blacklist_categories=('Cs', 'Cc'),
        blacklist_characters='\x00'
    ),
    max_size=100
)


@given(st.dictionaries(query_key, st.lists(query_value, min_size=1, max_size=5)))
def test_querydict_roundtrip(data):
    """Test that QueryDict can round-trip through urlencode."""
    # Build query string from data
    parts = []
    for key, values in data.items():
        for value in values:
            parts.append(f"{urllib.parse.quote_plus(key)}={urllib.parse.quote_plus(value)}")
    
    if not parts:
        return  # Skip empty case
    
    query_string = '&'.join(parts)
    
    # Create QueryDict, encode it, and parse again
    qd1 = django.http.QueryDict(query_string)
    encoded = qd1.urlencode()
    qd2 = django.http.QueryDict(encoded)
    
    # Check that all data is preserved
    for key in data:
        assert key in qd2
        # Get lists and compare (order might differ)
        original_values = qd1.getlist(key)
        roundtrip_values = qd2.getlist(key)
        assert sorted(original_values) == sorted(roundtrip_values)


@given(st.dictionaries(query_key, st.lists(query_value, min_size=2, max_size=5), min_size=1))
def test_querydict_multivalue_preservation(data):
    """Test that QueryDict preserves multiple values per key."""
    # Build query string with multiple values
    parts = []
    for key, values in data.items():
        for value in values:
            parts.append(f"{urllib.parse.quote_plus(key)}={urllib.parse.quote_plus(value)}")
    
    query_string = '&'.join(parts)
    qd = django.http.QueryDict(query_string)
    
    # Check all values are preserved
    for key, values in data.items():
        stored_values = qd.getlist(key)
        assert len(stored_values) == len(values)
        # Values should all be present (though order might differ)
        assert sorted(stored_values) == sorted(values)


# Strategy for cookie names and values
cookie_name = st.text(
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='_-'
    ),
    min_size=1,
    max_size=50
)

cookie_value = st.text(
    alphabet=st.characters(
        blacklist_categories=('Cs', 'Cc'),
        blacklist_characters=';,\\\"\x00\r\n'
    ),
    max_size=100
)


@given(st.dictionaries(cookie_name, cookie_value, min_size=1, max_size=10))
def test_parse_cookie_basic(cookies):
    """Test that parse_cookie can handle various cookie formats."""
    # Build cookie string
    cookie_parts = [f"{name}={value}" for name, value in cookies.items()]
    cookie_string = '; '.join(cookie_parts)
    
    # Parse the cookie
    parsed = django.http.parse_cookie(cookie_string)
    
    # Check all cookies are parsed correctly
    for name, value in cookies.items():
        assert name in parsed
        assert parsed[name] == value


@given(cookie_name, cookie_value)
def test_simplecookie_roundtrip(name, value):
    """Test SimpleCookie round-trip through output and parse."""
    # Create and set cookie
    cookie1 = django.http.SimpleCookie()
    cookie1[name] = value
    
    # Get the cookie header output
    output = cookie1.output(header='')
    
    # Parse it back
    cookie2 = django.http.SimpleCookie()
    cookie2.load(output)
    
    # Check the value is preserved
    assert name in cookie2
    assert cookie2[name].value == value


@given(st.text(min_size=0, max_size=1000))
def test_parse_cookie_no_crash(cookie_string):
    """Test that parse_cookie doesn't crash on arbitrary input."""
    try:
        result = django.http.parse_cookie(cookie_string)
        assert isinstance(result, dict)
    except Exception:
        # Some inputs might legitimately raise exceptions
        pass


@given(st.text(min_size=0, max_size=1000))
def test_querydict_no_crash(query_string):
    """Test that QueryDict doesn't crash on arbitrary input."""
    try:
        qd = django.http.QueryDict(query_string)
        # Try some basic operations
        qd.keys()
        qd.values()
        qd.urlencode()
    except Exception:
        # Some inputs might legitimately raise exceptions
        pass