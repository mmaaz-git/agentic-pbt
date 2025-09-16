"""Property-based tests for requests.sessions module"""

import string
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from requests.structures import CaseInsensitiveDict
from requests.cookies import cookiejar_from_dict, merge_cookies, RequestsCookieJar
from requests.sessions import merge_setting, SessionRedirectMixin
from collections import OrderedDict
import http.cookiejar as cookielib


# Strategy for valid HTTP header names (simplified)
header_name_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "-_",
    min_size=1,
    max_size=50
).filter(lambda x: not x.startswith("-") and not x.endswith("-"))

# Strategy for header values
header_value_strategy = st.text(min_size=0, max_size=200).filter(
    lambda x: "\n" not in x and "\r" not in x
)


@given(
    key=header_name_strategy,
    value=header_value_strategy,
    query_key=header_name_strategy
)
@settings(max_examples=1000)
def test_case_insensitive_dict_case_insensitivity(key, value, query_key):
    """Test that CaseInsensitiveDict retrieval is truly case-insensitive"""
    # Skip if keys are the same when lowercased but different otherwise
    # (undefined behavior per docstring)
    if key.lower() == query_key.lower() and key != query_key:
        cid = CaseInsensitiveDict()
        cid[key] = value
        
        # Should be able to retrieve with different case
        assert cid[query_key] == value
        assert cid[key.upper()] == value
        assert cid[key.lower()] == value
        
        # Contains check should also be case-insensitive
        assert query_key in cid
        assert key.upper() in cid
        assert key.lower() in cid


@given(
    base_key=st.text(alphabet=string.ascii_lowercase + string.digits + "-", min_size=1, max_size=20),
    value1=header_value_strategy,
    value2=header_value_strategy
)
@settings(suppress_health_check=[])
def test_case_insensitive_dict_last_key_case_preserved(base_key, value1, value2):
    """Test that CaseInsensitiveDict preserves the case of the last key set"""
    # Create two keys with same lowercase but different case
    key1 = base_key.lower()
    key2 = base_key.upper()
    
    if key1 != key2:  # Only test if they differ in case
        cid = CaseInsensitiveDict()
        cid[key1] = value1
        cid[key2] = value2  # Overwrites with different case
        
        # The iteration should contain the last case used
        keys_list = list(cid.keys())
        assert len(keys_list) == 1
        assert keys_list[0] == key2  # Should preserve case of last set


# Cookie name/value strategies
cookie_name_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "_-",
    min_size=1,
    max_size=30
)
cookie_value_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "!#$%&'*+-.^_`|~",
    min_size=0,
    max_size=100
)


@given(
    cookies1=st.dictionaries(cookie_name_strategy, cookie_value_strategy, max_size=10),
    cookies2=st.dictionaries(cookie_name_strategy, cookie_value_strategy, max_size=10)
)
def test_merge_cookies_preserves_all_unique_cookies(cookies1, cookies2):
    """Test that merge_cookies preserves all cookies when keys don't overlap"""
    # Create cookiejars
    jar1 = cookiejar_from_dict(cookies1)
    jar2 = cookiejar_from_dict(cookies2)
    
    # Merge
    merged = merge_cookies(jar1, jar2)
    
    # Extract cookies back
    merged_dict = {cookie.name: cookie.value for cookie in merged}
    
    # All cookies from jar2 should be in merged
    for name, value in cookies2.items():
        assert name in merged_dict
        assert merged_dict[name] == value
    
    # Cookies from jar1 that don't conflict should also be there
    for name, value in cookies1.items():
        if name not in cookies2:
            assert name in merged_dict
            assert merged_dict[name] == value


@given(
    base_dict=st.dictionaries(st.text(min_size=1, max_size=10), st.text(min_size=0, max_size=20)),
    override_dict=st.dictionaries(st.text(min_size=1, max_size=10), st.text(min_size=0, max_size=20)),
    none_keys=st.lists(st.text(min_size=1, max_size=10), max_size=5)
)
def test_merge_setting_removes_none_values(base_dict, override_dict, none_keys):
    """Test that merge_setting removes keys with None values"""
    # Add some None values to override_dict
    for key in none_keys:
        override_dict[key] = None
    
    # Merge settings
    merged = merge_setting(override_dict, base_dict, dict_class=OrderedDict)
    
    # Check that no None values exist in the result
    if merged is not None and isinstance(merged, dict):
        assert None not in merged.values()
        # Specifically check that none_keys are not in the result
        for key in none_keys:
            assert key not in merged


@given(
    request_setting=st.one_of(
        st.none(),
        st.text(min_size=0, max_size=20),
        st.dictionaries(st.text(min_size=1, max_size=10), st.text(min_size=0, max_size=20))
    ),
    session_setting=st.one_of(
        st.none(),
        st.text(min_size=0, max_size=20),
        st.dictionaries(st.text(min_size=1, max_size=10), st.text(min_size=0, max_size=20))
    )
)
def test_merge_setting_request_takes_precedence(request_setting, session_setting):
    """Test that request settings take precedence over session settings"""
    result = merge_setting(request_setting, session_setting)
    
    # If request_setting is not None and not a dict, it should be returned as-is
    if request_setting is not None:
        if not isinstance(request_setting, dict):
            assert result == request_setting
        elif not isinstance(session_setting, dict):
            # Non-dict session setting with dict request setting
            assert result == request_setting
    elif session_setting is not None:
        # Request is None, session is returned
        assert result == session_setting
    else:
        # Both None
        assert result is None


# URL strategies for testing should_strip_auth
url_strategy = st.builds(
    lambda scheme, host, port: f"{scheme}://{host}" + (f":{port}" if port else ""),
    scheme=st.sampled_from(["http", "https"]),
    host=st.text(alphabet=string.ascii_lowercase + string.digits + "-.", min_size=3, max_size=30)
         .filter(lambda x: not x.startswith(".") and not x.endswith(".") and ".." not in x),
    port=st.one_of(st.none(), st.integers(min_value=1, max_value=65535))
)


@given(
    host_base1=st.text(alphabet=string.ascii_lowercase, min_size=3, max_size=15),
    host_base2=st.text(alphabet=string.ascii_lowercase, min_size=3, max_size=15),
    old_scheme=st.sampled_from(["http", "https"]),
    new_scheme=st.sampled_from(["http", "https"])
)
def test_should_strip_auth_different_hosts(host_base1, host_base2, old_scheme, new_scheme):
    """Test that auth is stripped when redirecting to different hosts"""
    old_host = f"{host_base1}.example.com"
    new_host = f"{host_base2}.example.com"
    
    if old_host != new_host:  # Only test when hosts differ
        old_url = f"{old_scheme}://{old_host}"
        new_url = f"{new_scheme}://{new_host}"
        
        mixin = SessionRedirectMixin()
        # Different hosts should always strip auth
        assert mixin.should_strip_auth(old_url, new_url) == True


@given(
    host=st.text(alphabet=string.ascii_lowercase + ".", min_size=3, max_size=30)
        .filter(lambda x: "." in x and not x.startswith(".") and not x.endswith(".")),
)
def test_should_strip_auth_http_to_https_standard_ports(host):
    """Test special case: http->https on standard ports preserves auth"""
    old_url = f"http://{host}"  # Port 80 is implicit
    new_url = f"https://{host}"  # Port 443 is implicit
    
    mixin = SessionRedirectMixin()
    # This specific case should NOT strip auth (special case in the code)
    assert mixin.should_strip_auth(old_url, new_url) == False
    
    # But with explicit standard ports should also work
    old_url_explicit = f"http://{host}:80"
    new_url_explicit = f"https://{host}:443"
    assert mixin.should_strip_auth(old_url_explicit, new_url_explicit) == False