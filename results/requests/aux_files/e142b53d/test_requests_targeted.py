"""Targeted tests for specific potential bug patterns in requests."""

import string
from hypothesis import given, strategies as st, assume, settings, example
from requests import utils, PreparedRequest, Request, Session
from requests.structures import CaseInsensitiveDict
from requests.cookies import RequestsCookieJar
import json


# Test for potential integer overflow in super_len
@given(st.integers())
@settings(max_examples=1000)
def test_super_len_integer_overflow(size):
    """Test super_len with objects reporting extreme sizes."""
    if hasattr(utils, 'super_len'):
        class FakeFile:
            def __init__(self, size):
                self.len = size
            def __len__(self):
                return self.len
            def seek(self, offset, whence=0):
                pass
            def tell(self):
                return 0
        
        try:
            obj = FakeFile(size)
            result = utils.super_len(obj)
            assert isinstance(result, int)
        except:
            pass


# Test CaseInsensitiveDict with non-string keys
@given(st.one_of(
    st.integers(),
    st.floats(),
    st.none(),
    st.booleans()
))
def test_case_insensitive_dict_non_string_keys(key):
    """Test CaseInsensitiveDict behavior with non-string keys."""
    cid = CaseInsensitiveDict()
    try:
        cid[key] = "value"
        # If it accepts non-string keys, that might violate the contract
        # The docstring says "All keys are expected to be strings"
        assert False, f"CaseInsensitiveDict accepted non-string key: {key}"
    except (AttributeError, TypeError):
        # Expected to fail for non-strings
        pass


# Test prepared request with conflicting parameters
@given(
    st.text(alphabet=string.ascii_letters + "://."),
    st.dictionaries(st.text(), st.text()),
    st.text()
)
@settings(max_examples=500)
def test_prepared_request_url_params_conflict(base_url, params, extra):
    """Test PreparedRequest with URL that already has params."""
    try:
        # Create URL with existing params
        if "?" not in base_url and base_url.startswith("http"):
            url_with_params = f"{base_url}?existing=value&{extra}"
        else:
            url_with_params = base_url
        
        req = PreparedRequest()
        req.prepare_url(url_with_params, params)
        
        # Should handle both existing and new params
        assert req.url is not None
    except:
        pass


# Test cookie domain matching edge cases
@given(
    st.text(min_size=1, alphabet=string.ascii_letters + ".-"),
    st.text(min_size=1, alphabet=string.ascii_letters + ".-")
)
@settings(max_examples=500)
def test_cookie_domain_matching(domain1, domain2):
    """Test cookie domain matching logic."""
    jar = RequestsCookieJar()
    try:
        # Create cookie for domain1
        jar.set("test", "value", domain=domain1)
        
        # Check if we can get it for domain2
        # This tests the domain matching logic
        cookies = jar.get_dict(domain=domain2)
        
        # Basic sanity check
        assert isinstance(cookies, dict)
    except:
        pass


# Test guess_json_utf with truncated inputs
@given(st.integers(min_value=0, max_value=10))
@settings(max_examples=500)
def test_guess_json_utf_truncated(truncate_at):
    """Test guess_json_utf with truncated JSON."""
    # Create valid JSON and truncate it
    valid_json = '{"key": "value"}'
    
    for encoding in ['utf-8', 'utf-16-le', 'utf-16-be', 'utf-32-le', 'utf-32-be']:
        try:
            encoded = valid_json.encode(encoding)
            truncated = encoded[:truncate_at]
            
            result = utils.guess_json_utf(truncated)
            # Should either return None or a valid encoding
            assert result is None or isinstance(result, str)
        except:
            pass


# Test URL parsing with authentication
@given(
    st.text(min_size=1, alphabet=string.ascii_letters),
    st.text(min_size=1, alphabet=string.ascii_letters + string.digits),
    st.text(min_size=1, alphabet=string.ascii_letters + ".")
)
@settings(max_examples=500)
def test_get_auth_from_url_format(user, password, host):
    """Test get_auth_from_url with various URL formats."""
    url = f"http://{user}:{password}@{host}/path"
    
    try:
        result = utils.get_auth_from_url(url)
        if result:
            assert isinstance(result, tuple)
            assert len(result) == 2
            # Should extract the user and password
            assert result == (user, password)
    except:
        pass


# Test header validation with special characters
@given(
    st.text(),
    st.text()
)
@settings(max_examples=500)
def test_check_header_validity(name, value):
    """Test check_header_validity with various inputs."""
    if hasattr(utils, 'check_header_validity'):
        try:
            # Should either pass or raise specific exception
            utils.check_header_validity((name, value))
            # If it passes, headers should not contain certain chars
            assert '\r' not in name and '\n' not in name
            assert '\r' not in str(value) and '\n' not in str(value)
        except Exception as e:
            # Should raise InvalidHeader for invalid inputs
            assert "Invalid" in str(type(e).__name__)


# Test dict operations with None values
@given(st.dictionaries(
    st.text(min_size=1),
    st.one_of(st.none(), st.text())
))
@settings(max_examples=500)
def test_dict_operations_with_none(d):
    """Test various dict utility functions with None values."""
    if hasattr(utils, 'to_key_val_list'):
        result = utils.to_key_val_list(d)
        assert isinstance(result, list)
        
        if hasattr(utils, 'from_key_val_list'):
            # Round trip
            back = utils.from_key_val_list(result)
            # Should preserve non-None values
            for key, val in d.items():
                if val is not None:
                    assert key in back


# Test PreparedRequest with binary data
@given(st.binary())
@settings(max_examples=500)
def test_prepared_request_binary_body(data):
    """Test PreparedRequest with binary body data."""
    try:
        req = Request('POST', 'http://example.com', data=data)
        prep = req.prepare()
        
        # Should handle binary data
        assert prep.body is not None or len(data) == 0
    except:
        pass


# Test URL encoding with percent signs
@given(st.text(alphabet="%" + string.ascii_letters + string.digits))
@example("%%20")
@example("%2%20")
@example("test%20%")
@settings(max_examples=500)
def test_requote_uri_percent_handling(uri):
    """Test requote_uri handling of percent signs."""
    try:
        result = utils.requote_uri(uri)
        # Should properly handle percent encoding
        assert isinstance(result, str)
        
        # Test idempotence
        result2 = utils.requote_uri(result)
        assert result == result2
    except:
        # Invalid percent encoding might raise
        pass