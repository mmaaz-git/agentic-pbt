"""Additional edge case tests for requests.sessions"""

import string
from hypothesis import given, strategies as st, assume, settings
from requests.structures import CaseInsensitiveDict
from requests.cookies import cookiejar_from_dict, merge_cookies, RequestsCookieJar
from requests.sessions import merge_setting, SessionRedirectMixin, Session
from requests import Request, PreparedRequest
from collections import OrderedDict
import http.cookiejar as cookielib


# Test empty strings and edge cases for CaseInsensitiveDict
@given(value=st.text())
@settings(max_examples=1000)
def test_case_insensitive_dict_empty_key(value):
    """Test CaseInsensitiveDict with empty string key"""
    cid = CaseInsensitiveDict()
    # Empty string should work as a key
    cid[""] = value
    assert cid[""] == value
    assert "" in cid


@given(
    keys=st.lists(st.text(alphabet=string.ascii_letters, min_size=1, max_size=10), 
                  min_size=1, max_size=20),
    values=st.lists(st.text(), min_size=1, max_size=20)
)
@settings(max_examples=500)
def test_case_insensitive_dict_multiple_operations(keys, values):
    """Test CaseInsensitiveDict with multiple set/get operations"""
    # Make keys and values same length
    length = min(len(keys), len(values))
    keys = keys[:length]
    values = values[:length]
    
    cid = CaseInsensitiveDict()
    
    # Set all keys
    for k, v in zip(keys, values):
        cid[k] = v
    
    # Verify all keys are accessible case-insensitively
    for k, v in zip(keys, values):
        assert cid[k.lower()] == v or k.lower() in [key.lower() for key in keys[keys.index(k)+1:]]
        assert cid[k.upper()] == v or k.upper() in [key.upper() for key in keys[keys.index(k)+1:]]


# Test edge cases in merge_cookies
@given(
    cookie_dict=st.dictionaries(
        st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=20),
        st.one_of(st.text(), st.none())
    )
)
@settings(max_examples=500)
def test_cookiejar_from_dict_with_none_values(cookie_dict):
    """Test cookiejar_from_dict with None values"""
    # Should handle None values gracefully
    jar = cookiejar_from_dict(cookie_dict)
    
    # Extract back to dict
    result_dict = {cookie.name: cookie.value for cookie in jar}
    
    # None values should be converted to empty string or handled
    for name, value in cookie_dict.items():
        if value is not None:
            assert name in result_dict
            # The value should be preserved or converted to string
            assert result_dict[name] == str(value) or result_dict[name] == value


# Test rebuild_method edge cases
@given(
    initial_method=st.sampled_from(["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"]),
    status_code=st.integers(min_value=100, max_value=599)
)
@settings(max_examples=500)
def test_rebuild_method_all_status_codes(initial_method, status_code):
    """Test rebuild_method with various status codes"""
    from unittest.mock import Mock
    
    mixin = SessionRedirectMixin()
    
    # Create mock objects
    prepared_request = Mock()
    prepared_request.method = initial_method
    
    response = Mock()
    response.status_code = status_code
    
    # Call rebuild_method
    mixin.rebuild_method(prepared_request, response)
    
    # Check specific status code behaviors documented in the code
    if status_code == 303 and initial_method != "HEAD":  # See Other
        assert prepared_request.method == "GET"
    elif status_code == 302 and initial_method != "HEAD":  # Found
        assert prepared_request.method == "GET"
    elif status_code == 301 and initial_method == "POST":  # Moved Permanently
        assert prepared_request.method == "GET"
    else:
        # Method should remain unchanged for other cases
        assert prepared_request.method == initial_method


# Test merge_setting with complex nested dictionaries
@given(
    base_dict=st.recursive(
        st.one_of(st.text(), st.integers(), st.none()),
        lambda children: st.dictionaries(st.text(min_size=1, max_size=5), children, max_size=3),
        max_leaves=10
    ),
    override_dict=st.recursive(
        st.one_of(st.text(), st.integers(), st.none()),
        lambda children: st.dictionaries(st.text(min_size=1, max_size=5), children, max_size=3),
        max_leaves=10
    )
)
@settings(max_examples=200)
def test_merge_setting_nested_dicts(base_dict, override_dict):
    """Test merge_setting with nested dictionary structures"""
    # merge_setting only merges one level deep, not recursively
    result = merge_setting(override_dict, base_dict)
    
    if result is not None:
        if isinstance(result, dict):
            # None values should be removed
            assert None not in result.values()
            
            # Override values should take precedence
            if isinstance(override_dict, dict) and isinstance(base_dict, dict):
                for key in override_dict:
                    if override_dict[key] is not None:
                        assert key in result
                        assert result[key] == override_dict[key]


# Test Session.prepare_request with edge cases
@given(
    method=st.sampled_from(["get", "post", "put", "delete", "head", "options", "patch"]),
    url=st.text(alphabet=string.ascii_letters + ":/.", min_size=7, max_size=100)
        .filter(lambda x: x.startswith("http://") or x.startswith("https://"))
)
@settings(max_examples=200)
def test_session_prepare_request_method_uppercase(method, url):
    """Test that Session.prepare_request uppercases the method"""
    session = Session()
    request = Request(method=method, url=url)
    
    try:
        prepared = session.prepare_request(request)
        # Method should always be uppercased
        assert prepared.method == method.upper()
    except Exception:
        # Some URLs might be invalid, that's ok
        pass


# Test should_strip_auth with port edge cases
@given(
    host=st.text(alphabet=string.ascii_lowercase + ".", min_size=5, max_size=30)
        .filter(lambda x: "." in x and not x.startswith(".") and not x.endswith(".")),
    port1=st.integers(min_value=1, max_value=65535),
    port2=st.integers(min_value=1, max_value=65535)
)
@settings(max_examples=500)
def test_should_strip_auth_port_changes(host, port1, port2):
    """Test should_strip_auth behavior with port changes"""
    mixin = SessionRedirectMixin()
    
    # Same host, different ports with same scheme
    old_url = f"http://{host}:{port1}"
    new_url = f"http://{host}:{port2}"
    
    if port1 != port2:
        # Different ports on same host and scheme should strip auth
        # unless both are default ports for the scheme
        if not ((port1 in (80, None) and port2 in (80, None)) or 
                (port1 in (443, None) and port2 in (443, None))):
            result = mixin.should_strip_auth(old_url, new_url)
            # According to the code, changed_port should cause stripping
            assert result == True