import django
from django.conf import settings
import django.apps

# Configure Django settings with apps
settings.configure(
    DEBUG=True,
    SECRET_KEY='test-secret-key',
    USE_I18N=True,
    USE_L10N=True,
    USE_TZ=True,
    LANGUAGE_CODE='en-us',
    INSTALLED_APPS=[
        'django.contrib.humanize',
    ],
)

# Initialize Django apps
django.setup()

from hypothesis import given, strategies as st, assume, settings as hyp_settings
import pytest
import math
import re

# Import modules to test
from django.contrib.humanize.templatetags import humanize
from django.utils import text, encoding


# Test 1: IRI to URI round-trip for ASCII characters
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$&\'()*+,/:;=?@[]~', min_size=1))
def test_iri_uri_roundtrip_ascii(iri):
    """For ASCII input without reserved chars, IRI to URI and back should preserve the input"""
    uri = encoding.iri_to_uri(iri)
    back = encoding.uri_to_iri(uri)
    assert back == iri


# Test 2: IRI to URI round-trip for all ASCII
@given(st.text(min_size=1, max_size=100).filter(lambda s: all(ord(c) < 128 for c in s)))
def test_iri_uri_roundtrip_all_ascii(iri):
    """Test IRI/URI round-trip for all ASCII characters"""
    uri = encoding.iri_to_uri(iri)
    back = encoding.uri_to_iri(uri)
    # This will reveal which characters don't round-trip
    assert back == iri, f"Failed round-trip: {repr(iri)} -> {repr(uri)} -> {repr(back)}"


# Test 3: punycode with valid domain names
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-', min_size=1, max_size=63)
       .filter(lambda s: not s.startswith('-') and not s.endswith('-')))
def test_punycode_valid_ascii_domains(domain):
    """ASCII domains should remain unchanged by punycode (except for case)"""
    result = encoding.punycode(domain)
    assert result == domain.lower()


# Test 4: capfirst with ASCII letters
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ', min_size=1))
def test_capfirst_ascii_letters(s):
    """capfirst should capitalize the first ASCII letter"""
    result = text.capfirst(s)
    if s[0].isalpha() and ord(s[0]) < 128:  # ASCII letter
        assert result[0].isupper()
        if len(s) > 1:
            assert result[1:] == s[1:]
    else:
        assert result == s


# Test 5: ordinal function
@given(st.integers(min_value=0, max_value=10000))
def test_ordinal_non_negative(n):
    """ordinal should work for any non-negative integer"""
    result = humanize.ordinal(n)
    assert isinstance(result, str)
    assert str(n) in result
    
    # Check correct suffix
    if n % 100 in (11, 12, 13):
        assert 'th' in result
    elif n % 10 == 1:
        assert 'st' in result
    elif n % 10 == 2:
        assert 'nd' in result
    elif n % 10 == 3:
        assert 'rd' in result
    else:
        assert 'th' in result


# Test 6: apnumber for 1-9
@given(st.integers(min_value=1, max_value=9))
def test_apnumber_one_to_nine(n):
    """apnumber should convert 1-9 to words"""
    result = humanize.apnumber(n)
    expected = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    assert result == expected[n-1]


# Test 7: slugify idempotence
@given(st.text())
def test_slugify_idempotence(s):
    """Applying slugify twice should give the same result as applying it once"""
    once = text.slugify(s)
    twice = text.slugify(once)
    assert once == twice