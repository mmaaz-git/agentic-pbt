import django
from django.conf import settings

# Configure Django settings
settings.configure(
    DEBUG=True,
    SECRET_KEY='test-secret-key',
    USE_I18N=True,
    USE_L10N=True,
    USE_TZ=True,
)

from hypothesis import given, strategies as st, assume, settings as hyp_settings
import pytest
import math
import re

# Import modules to test
from django.contrib.humanize.templatetags import humanize
from django.utils import text, encoding


# Test 1: slugify idempotence property
@given(st.text())
def test_slugify_idempotence(s):
    """Applying slugify twice should give the same result as applying it once"""
    once = text.slugify(s)
    twice = text.slugify(once)
    assert once == twice, f"slugify not idempotent: '{s}' -> '{once}' -> '{twice}'"


# Test 2: phone2numeric case insensitivity
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-() +.'))
def test_phone2numeric_case_insensitive(phone):
    """phone2numeric should handle uppercase and lowercase the same way"""
    result_lower = text.phone2numeric(phone.lower())
    result_upper = text.phone2numeric(phone.upper())
    assert result_lower == result_upper


# Test 3: phone2numeric idempotence for numeric inputs
@given(st.text(alphabet='0123456789-() +.'))
def test_phone2numeric_numeric_idempotent(phone):
    """phone2numeric should not change purely numeric phone numbers"""
    result = text.phone2numeric(phone)
    # The function lowercases, so we need to compare with lowercased input
    assert result == phone.lower()


# Test 4: ordinal function for non-negative integers
@given(st.integers(min_value=0, max_value=10000))
def test_ordinal_non_negative(n):
    """ordinal should work for any non-negative integer as documented"""
    result = humanize.ordinal(n)
    assert isinstance(result, str)
    assert str(n) in result  # The number should appear in the result
    
    # Check correct suffix based on the rules
    if n % 100 in (11, 12, 13):
        assert result.endswith('th')
    elif n % 10 == 1:
        assert result.endswith('st')
    elif n % 10 == 2:
        assert result.endswith('nd')
    elif n % 10 == 3:
        assert result.endswith('rd')
    else:
        assert result.endswith('th')


# Test 5: ordinal handles negative integers correctly  
@given(st.integers(max_value=-1))
def test_ordinal_negative(n):
    """ordinal should return string representation for negative integers"""
    result = humanize.ordinal(n)
    assert result == str(n)  # Documentation says it returns str(value) for negative


# Test 6: apnumber property - numbers 1-9 become words
@given(st.integers(min_value=1, max_value=9))
def test_apnumber_one_to_nine(n):
    """apnumber should convert 1-9 to words"""
    result = humanize.apnumber(n)
    expected = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    # The function returns localized strings, but the English words should be in there
    assert isinstance(result, str)
    assert result != str(n)  # Should not be the number itself


# Test 7: apnumber property - other numbers stay as is
@given(st.integers().filter(lambda x: x < 1 or x > 9))
def test_apnumber_outside_range(n):
    """apnumber should return the number itself for values outside 1-9"""
    result = humanize.apnumber(n)
    assert result == n


# Test 8: camel_case_to_spaces removes camel casing
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'))
def test_camel_case_to_spaces_lowercase(s):
    """camel_case_to_spaces should always produce lowercase output"""
    result = text.camel_case_to_spaces(s)
    assert result == result.lower()


# Test 9: camel_case_to_spaces strips whitespace
@given(st.text())
def test_camel_case_to_spaces_strips(s):
    """camel_case_to_spaces should strip surrounding whitespace"""
    result = text.camel_case_to_spaces(s)
    assert result == result.strip()


# Test 10: IRI to URI and back (round-trip property)
@given(st.text(min_size=1))
@hyp_settings(max_examples=200)
def test_iri_uri_roundtrip(iri):
    """Converting IRI to URI and back might preserve certain properties"""
    try:
        uri = encoding.iri_to_uri(iri)
        back = encoding.uri_to_iri(uri)
        
        # The round-trip might not be perfect due to normalization,
        # but certain properties should hold
        # Let's check if ASCII characters are preserved
        ascii_chars = ''.join(c for c in iri if ord(c) < 128)
        ascii_back = ''.join(c for c in back if ord(c) < 128)
        
        # For purely ASCII input, round-trip should work
        if all(ord(c) < 128 for c in iri):
            assert back == iri
    except (UnicodeError, ValueError) as e:
        # Some invalid inputs might cause errors
        pass


# Test 11: punycode domain encoding
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-.', min_size=1, max_size=63))
def test_punycode_ascii_domains(domain):
    """ASCII domains should remain unchanged by punycode"""
    result = encoding.punycode(domain)
    assert result == domain.lower()  # punycode lowercases ASCII domains


# Test 12: intcomma property - idempotence for strings
@given(st.text(alphabet='0123456789,'))
def test_intcomma_string_idempotence(s):
    """intcomma should be idempotent for already-formatted strings"""
    result1 = humanize.intcomma(s, use_l10n=False)
    result2 = humanize.intcomma(result1, use_l10n=False)
    assert result1 == result2


# Test 13: Test capfirst actually capitalizes first letter
@given(st.text(min_size=1))
def test_capfirst_capitalizes(s):
    """capfirst should capitalize the first character if it's a letter"""
    result = text.capfirst(s)
    if s and s[0].isalpha():
        assert result[0].isupper()
        # Rest should be unchanged
        if len(s) > 1:
            assert result[1:] == s[1:]
    else:
        assert result == s  # Non-letter first char unchanged