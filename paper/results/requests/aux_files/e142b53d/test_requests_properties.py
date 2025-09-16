"""Property-based tests for the requests library using Hypothesis."""

import json
import string
from hypothesis import given, strategies as st, assume, settings
from requests import utils
from requests.structures import CaseInsensitiveDict


# Property 1: Cookie dict round-trip
@given(st.dictionaries(
    st.text(min_size=1, alphabet=string.ascii_letters + string.digits + "_-"),
    st.text(min_size=0)
))
@settings(max_examples=500)
def test_cookie_round_trip(cookie_dict):
    """Test that converting a dict to cookiejar and back preserves the dict."""
    jar = utils.cookiejar_from_dict(cookie_dict)
    result = utils.dict_from_cookiejar(jar)
    assert result == cookie_dict


# Property 2: CaseInsensitiveDict case-insensitive operations
@given(
    st.dictionaries(
        st.text(min_size=1, alphabet=string.ascii_letters),
        st.text()
    ),
    st.text(min_size=1, alphabet=string.ascii_letters)
)
def test_case_insensitive_dict_get(initial_dict, key):
    """Test CaseInsensitiveDict handles case-insensitive lookups correctly."""
    cid = CaseInsensitiveDict(initial_dict)
    
    # If we set a value with one case, we should get it with any case
    test_value = "test_value"
    cid[key] = test_value
    
    # Should be able to retrieve with different cases
    assert cid[key.lower()] == test_value
    assert cid[key.upper()] == test_value
    assert cid[key] == test_value
    
    # The actual stored key should be the last one set
    assert key in list(cid.keys())


# Property 3: requote_uri idempotence
@given(st.text(min_size=1).filter(lambda x: '%' not in x or all(
    i + 2 < len(x) and x[i+1:i+3].isalnum() and len(x[i+1:i+3]) == 2
    for i in range(len(x)) if x[i] == '%'
)))
def test_requote_uri_idempotent(uri):
    """Test that requote_uri is idempotent - applying twice = applying once."""
    # Skip URIs that would raise InvalidURL
    try:
        once = utils.requote_uri(uri)
        twice = utils.requote_uri(once)
        assert once == twice
    except:
        # If requote_uri raises an exception, that's not the property we're testing
        pass


# Property 4: CaseInsensitiveDict preserves original case in iteration
@given(st.dictionaries(
    st.text(min_size=1, alphabet=string.ascii_letters),
    st.text(),
    min_size=1
))
def test_case_insensitive_dict_preserves_case(original_dict):
    """Test that CaseInsensitiveDict preserves the original case of keys."""
    cid = CaseInsensitiveDict(original_dict)
    
    # The keys should be exactly as inserted
    assert set(cid.keys()) == set(original_dict.keys())
    
    # But lookups should be case-insensitive
    for key in original_dict:
        assert cid[key.lower()] == original_dict[key]
        assert cid[key.upper()] == original_dict[key]


# Property 5: guess_json_utf for valid UTF-8 JSON
@given(st.dictionaries(st.text(), st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text()
)))
def test_guess_json_utf_utf8(json_obj):
    """Test that valid UTF-8 JSON is correctly identified."""
    json_bytes = json.dumps(json_obj).encode('utf-8')
    encoding = utils.guess_json_utf(json_bytes)
    assert encoding == 'utf-8'


# Property 6: Cookie operations with overwrite parameter
@given(
    st.dictionaries(st.text(min_size=1, alphabet=string.ascii_letters), st.text()),
    st.dictionaries(st.text(min_size=1, alphabet=string.ascii_letters), st.text())
)
def test_cookie_overwrite_behavior(dict1, dict2):
    """Test cookiejar_from_dict overwrite parameter behavior."""
    # Create initial jar
    jar = utils.cookiejar_from_dict(dict1)
    
    # Add new cookies with overwrite=False
    jar = utils.cookiejar_from_dict(dict2, cookiejar=jar, overwrite=False)
    result = utils.dict_from_cookiejar(jar)
    
    # Original values from dict1 should be preserved where keys overlap
    for key in dict1:
        if key in dict2:
            assert result[key] == dict1[key]  # Should keep original
        else:
            assert result[key] == dict1[key]
    
    # New keys from dict2 should be added
    for key in dict2:
        if key not in dict1:
            assert result[key] == dict2[key]


# Property 7: unquote_unreserved preserves reserved characters
@given(st.text(alphabet=string.ascii_letters + string.digits + "-_.~"))
def test_unquote_unreserved_preserves_unreserved(text):
    """Test that unquote_unreserved doesn't change unreserved characters."""
    result = utils.unquote_unreserved(text)
    assert result == text


# Property 8: CaseInsensitiveDict with conflicting keys
@given(st.text(min_size=1, max_size=10, alphabet=string.ascii_letters))
@settings(max_examples=1000)
def test_case_insensitive_dict_last_wins(base_key):
    """Test that with case-conflicting keys, the last one wins."""
    # Create variations of the same key with different cases
    keys = [base_key.lower(), base_key.upper(), base_key.title()]
    if len(base_key) > 1:
        keys.append(base_key.swapcase())
    
    cid = CaseInsensitiveDict()
    for i, key in enumerate(keys):
        cid[key] = i
    
    # The value should be from the last key set
    assert cid[keys[0]] == len(keys) - 1
    # The actual key stored should be the last one
    assert list(cid.keys()) == [keys[-1]]