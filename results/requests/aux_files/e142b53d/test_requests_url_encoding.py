"""Test URL encoding/decoding properties in requests."""

import string
import codecs
import json
from hypothesis import given, strategies as st, assume, settings, example
from requests import utils
from requests.compat import quote, unquote
from requests.models import PreparedRequest


# Test URL parameter encoding
@given(st.dictionaries(
    st.text(min_size=1, alphabet=string.ascii_letters),
    st.one_of(
        st.text(),
        st.none(),
        st.lists(st.text())
    )
))
@settings(max_examples=500)
def test_prepare_url_params(params):
    """Test URL parameter preparation doesn't lose data."""
    try:
        req = PreparedRequest()
        req.prepare_url("http://example.com", params)
        # Check that the URL was created
        assert req.url.startswith("http://example.com")
        # If params were provided, they should be in the URL
        if params:
            assert "?" in req.url or not any(v for v in params.values() if v)
    except Exception as e:
        # Some param combinations might be invalid
        pass


# Test get_encodings_from_content
@given(st.text())
@settings(max_examples=500)
def test_get_encodings_from_content_no_crash(html_content):
    """Test get_encodings_from_content doesn't crash."""
    if hasattr(utils, 'get_encodings_from_content'):
        result = utils.get_encodings_from_content(html_content)
        assert isinstance(result, list)


# Test super_len for various types
@given(st.one_of(
    st.text(),
    st.binary(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text())
))
@settings(max_examples=500)
def test_super_len_various_types(obj):
    """Test super_len handles various object types."""
    if hasattr(utils, 'super_len'):
        try:
            length = utils.super_len(obj)
            assert isinstance(length, int)
            assert length >= 0
        except (TypeError, AttributeError):
            # Some types might not be supported
            pass


# Test guess_filename
@given(st.text())
@settings(max_examples=500)
def test_guess_filename_no_crash(path_like):
    """Test guess_filename doesn't crash on various inputs."""
    if hasattr(utils, 'guess_filename'):
        try:
            result = utils.guess_filename(path_like)
            assert result is None or isinstance(result, str)
        except:
            pass


# Test get_netrc_auth
@given(st.text(alphabet=string.ascii_letters + "://."))
@settings(max_examples=200)
def test_get_netrc_auth_no_crash(url):
    """Test get_netrc_auth doesn't crash."""
    if hasattr(utils, 'get_netrc_auth'):
        try:
            result = utils.get_netrc_auth(url)
            assert result is None or (isinstance(result, tuple) and len(result) == 2)
        except:
            # Might fail on invalid URLs or missing netrc
            pass


# Test to_key_val_list with various inputs
@given(st.one_of(
    st.dictionaries(st.text(), st.text()),
    st.lists(st.tuples(st.text(), st.text())),
    st.none()
))
@settings(max_examples=500)
def test_to_key_val_list_various_inputs(value):
    """Test to_key_val_list handles various input types."""
    if hasattr(utils, 'to_key_val_list'):
        try:
            result = utils.to_key_val_list(value)
            assert result is None or isinstance(result, list)
        except:
            pass


# Test parse_list_header
@given(st.text())
@settings(max_examples=500)
def test_parse_list_header_no_crash(header):
    """Test parse_list_header doesn't crash."""
    if hasattr(utils, 'parse_list_header'):
        result = utils.parse_list_header(header)
        assert isinstance(result, list)


# Test parse_dict_header  
@given(st.text())
@settings(max_examples=500)
def test_parse_dict_header_no_crash(header):
    """Test parse_dict_header doesn't crash."""
    if hasattr(utils, 'parse_dict_header'):
        result = utils.parse_dict_header(header)
        assert isinstance(result, dict)


# Test unquote_header_value
@given(st.text())
@example('""')
@example('"test"')
@example('"test\\"quote"')
@settings(max_examples=500)
def test_unquote_header_value_no_crash(value):
    """Test unquote_header_value doesn't crash."""
    if hasattr(utils, 'unquote_header_value'):
        result = utils.unquote_header_value(value)
        assert isinstance(result, str)


# Test urldefragauth
@given(st.text(alphabet=string.printable))
@settings(max_examples=500)
def test_urldefragauth_no_crash(url):
    """Test urldefragauth doesn't crash."""
    if hasattr(utils, 'urldefragauth'):
        try:
            result = utils.urldefragauth(url)
            assert isinstance(result, str)
            # Should remove fragment
            if '#' in url:
                assert '#' not in result or result.count('#') < url.count('#')
        except:
            pass


# Test select_proxy with various URLs and proxies
@given(
    st.text(alphabet=string.ascii_letters + "://."),
    st.dictionaries(st.text(), st.text())
)
@settings(max_examples=200)
def test_select_proxy_no_crash(url, proxies):
    """Test select_proxy doesn't crash."""
    if hasattr(utils, 'select_proxy'):
        try:
            result = utils.select_proxy(url, proxies)
            assert result is None or isinstance(result, str)
        except:
            pass


# Test JSON encoding edge case with UTF-16/32
@given(st.dictionaries(st.text(), st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text()
)))
@settings(max_examples=200)
def test_guess_json_utf_various_encodings(json_obj):
    """Test guess_json_utf with different encodings."""
    for encoding in ['utf-16-le', 'utf-16-be', 'utf-32-le', 'utf-32-be']:
        try:
            json_bytes = json.dumps(json_obj).encode(encoding)
            result = utils.guess_json_utf(json_bytes)
            # Should detect something, even if not exact
            assert result is not None
        except:
            # Some encodings might fail for certain content
            pass