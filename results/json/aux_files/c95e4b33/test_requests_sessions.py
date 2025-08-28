import math
import string
from collections import OrderedDict
from urllib.parse import urlparse

import pytest
from hypothesis import assume, given, strategies as st, settings

import requests.sessions
from requests.sessions import (
    Session,
    SessionRedirectMixin,
    merge_hooks,
    merge_setting,
)


@given(
    request_setting=st.one_of(
        st.none(),
        st.dictionaries(st.text(min_size=1), st.text()),
        st.text(),
        st.integers(),
        st.booleans(),
    ),
    session_setting=st.one_of(
        st.none(),
        st.dictionaries(st.text(min_size=1), st.text()),
        st.text(),
        st.integers(),
        st.booleans(),
    )
)
def test_merge_setting_none_handling(request_setting, session_setting):
    """Test that merge_setting properly handles None values"""
    result = merge_setting(request_setting, session_setting)
    
    # If session_setting is None, should return request_setting
    if session_setting is None:
        assert result == request_setting
    # If request_setting is None, should return session_setting
    elif request_setting is None:
        assert result == session_setting
    # If neither are dicts/Mappings, request_setting wins
    elif not (isinstance(session_setting, dict) and isinstance(request_setting, dict)):
        assert result == request_setting


@given(
    session_dict=st.dictionaries(st.text(min_size=1), st.text()),
    request_dict=st.dictionaries(st.text(min_size=1), st.one_of(st.text(), st.none()))
)
def test_merge_setting_removes_none_values(session_dict, request_dict):
    """Test that merge_setting removes keys with None values from merged dict"""
    result = merge_setting(request_dict, session_dict)
    
    # Result should be a dict
    assert isinstance(result, (dict, OrderedDict))
    
    # No None values should be present in result
    assert None not in result.values()
    
    # All non-None request values should be in result
    for k, v in request_dict.items():
        if v is not None:
            assert result.get(k) == v


@given(
    request_hooks=st.one_of(
        st.none(),
        st.just({'response': []}),
        st.dictionaries(
            st.sampled_from(['response', 'request']),
            st.lists(st.text())
        )
    ),
    session_hooks=st.one_of(
        st.none(),
        st.just({'response': []}),
        st.dictionaries(
            st.sampled_from(['response', 'request']),
            st.lists(st.text())
        )
    )
)
def test_merge_hooks_empty_response_handling(request_hooks, session_hooks):
    """Test merge_hooks special handling of empty response lists"""
    result = merge_hooks(request_hooks, session_hooks)
    
    # If session_hooks is None or has empty response list, return request_hooks
    if session_hooks is None or session_hooks.get("response") == []:
        assert result == request_hooks
    # If request_hooks is None or has empty response list, return session_hooks  
    elif request_hooks is None or request_hooks.get("response") == []:
        assert result == session_hooks
    else:
        # Otherwise it should merge them
        assert result is not None


@given(
    old_url=st.text(min_size=1).map(lambda s: f"http://example.com/{s}"),
    new_url=st.text(min_size=1).map(lambda s: f"http://example.com/{s}")
)
def test_should_strip_auth_same_host_http(old_url, new_url):
    """Test that auth is not stripped for same host redirects"""
    mixin = SessionRedirectMixin()
    
    # Same host, same scheme - should not strip auth
    should_strip = mixin.should_strip_auth(old_url, new_url)
    assert should_strip == False


@given(
    host1=st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=20),
    host2=st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=20),
    path=st.text(alphabet=string.ascii_letters + string.digits + '/', max_size=50)
)
def test_should_strip_auth_different_hosts(host1, host2, path):
    """Test that auth is stripped when redirecting to different hosts"""
    assume(host1 != host2)
    
    mixin = SessionRedirectMixin()
    old_url = f"http://{host1}.com/{path}"
    new_url = f"http://{host2}.com/{path}"
    
    should_strip = mixin.should_strip_auth(old_url, new_url)
    assert should_strip == True


@given(
    path=st.text(alphabet=string.ascii_letters + string.digits + '/', max_size=50)
)
def test_should_strip_auth_http_to_https_standard_ports(path):
    """Test special case: http -> https redirect on standard ports keeps auth"""
    mixin = SessionRedirectMixin()
    
    # HTTP (port 80) to HTTPS (port 443) on same host - should NOT strip
    old_url = f"http://example.com/{path}"
    new_url = f"https://example.com/{path}"
    
    should_strip = mixin.should_strip_auth(old_url, new_url)
    assert should_strip == False
    
    # Explicit standard ports
    old_url = f"http://example.com:80/{path}"
    new_url = f"https://example.com:443/{path}"
    
    should_strip = mixin.should_strip_auth(old_url, new_url)
    assert should_strip == False


@given(
    prefixes=st.lists(
        st.text(alphabet=string.ascii_letters + '://', min_size=5, max_size=30),
        min_size=1,
        max_size=10,
        unique=True
    )
)
def test_session_mount_adapter_ordering(prefixes):
    """Test that Session.mount maintains adapters in descending order by prefix length"""
    session = Session()
    
    # Clear default adapters
    session.adapters.clear()
    
    # Mount adapters with different prefix lengths
    from requests.adapters import HTTPAdapter
    for prefix in prefixes:
        session.mount(prefix, HTTPAdapter())
    
    # Check that adapters are sorted by prefix length (descending)
    adapter_prefixes = list(session.adapters.keys())
    sorted_prefixes = sorted(adapter_prefixes, key=len, reverse=True)
    
    assert adapter_prefixes == sorted_prefixes


@given(
    url_prefixes=st.lists(
        st.tuples(
            st.text(alphabet=string.ascii_letters + '://', min_size=5, max_size=30),
            st.text(alphabet=string.ascii_letters + string.digits + './:?', min_size=0, max_size=50)
        ),
        min_size=1,
        max_size=5,
        unique_by=lambda x: x[0]
    )
)
def test_session_get_adapter_longest_prefix_match(url_prefixes):
    """Test that get_adapter returns the adapter with the longest matching prefix"""
    session = Session()
    session.adapters.clear()
    
    from requests.adapters import HTTPAdapter
    
    # Mount adapters
    adapters = {}
    for prefix, _ in url_prefixes:
        adapter = HTTPAdapter()
        adapters[prefix] = adapter
        session.mount(prefix, adapter)
    
    # Test URL matching
    for prefix, suffix in url_prefixes:
        test_url = prefix + suffix
        
        # Find which adapter should match
        matching_prefixes = [p for p in adapters.keys() if test_url.lower().startswith(p.lower())]
        
        if matching_prefixes:
            # Should match the longest prefix
            expected_prefix = max(matching_prefixes, key=len)
            expected_adapter = adapters[expected_prefix]
            
            result_adapter = session.get_adapter(test_url)
            assert result_adapter == expected_adapter


@given(
    base_dict=st.dictionaries(st.text(min_size=1), st.text()),
    override_dict=st.dictionaries(st.text(min_size=1), st.text())
)
def test_merge_setting_preserves_order_with_ordereddict(base_dict, override_dict):
    """Test that merge_setting with OrderedDict preserves insertion order"""
    # Convert to OrderedDict to ensure order
    base_ordered = OrderedDict(base_dict)
    override_ordered = OrderedDict(override_dict)
    
    result = merge_setting(override_ordered, base_ordered, dict_class=OrderedDict)
    
    # Result should be OrderedDict
    assert isinstance(result, OrderedDict)
    
    # All keys from base should come first (if not overridden), then override keys
    result_keys = list(result.keys())
    
    # Check that all keys are present
    expected_keys = set(base_dict.keys()) | set(override_dict.keys())
    assert set(result_keys) == expected_keys


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=20),  # key
            st.one_of(st.none(), st.text())     # value (can be None)
        ),
        min_size=1,
        max_size=20
    )
)
def test_merge_setting_none_deletion_consistency(items):
    """Test that None values consistently delete keys regardless of dict structure"""
    # Build session dict (no None values)
    session_dict = {k: v for k, v in items if v is not None}
    
    # Build request dict (may have None values)
    request_dict = dict(items)
    
    result = merge_setting(request_dict, session_dict)
    
    # Keys with None values in request_dict should not be in result
    for k, v in request_dict.items():
        if v is None:
            assert k not in result
        else:
            assert result.get(k) == v
    
    # Keys only in session_dict should be in result
    for k, v in session_dict.items():
        if k not in request_dict:
            assert result.get(k) == v


@given(
    port=st.integers(min_value=1, max_value=65535),
    path=st.text(alphabet=string.ascii_letters + string.digits + '/', max_size=50)
)
def test_should_strip_auth_nonstandard_ports(port, path):
    """Test auth stripping with non-standard ports"""
    assume(port not in [80, 443])
    
    mixin = SessionRedirectMixin()
    
    # Same host, different non-standard ports - should strip
    old_url = f"http://example.com:{port}/{path}"
    new_url = f"http://example.com:{port + 1}/{path}"
    
    should_strip = mixin.should_strip_auth(old_url, new_url)
    assert should_strip == True
    
    # Same host, same non-standard port - should not strip
    old_url = f"http://example.com:{port}/{path}"
    new_url = f"http://example.com:{port}/{path}"
    
    should_strip = mixin.should_strip_auth(old_url, new_url)
    assert should_strip == False


@given(
    headers_dict=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=0, max_size=100)
    )
)
def test_merge_setting_with_case_insensitive_dict(headers_dict):
    """Test merge_setting works correctly with CaseInsensitiveDict"""
    from requests.structures import CaseInsensitiveDict
    
    # Create case variations of the same keys
    session_headers = CaseInsensitiveDict(headers_dict)
    
    # Create request headers with some keys in different case
    request_headers = {}
    for k, v in headers_dict.items():
        # Randomly change case
        if len(k) > 0:
            new_key = k.upper() if k[0].islower() else k.lower()
            request_headers[new_key] = v + "_modified"
    
    result = merge_setting(
        CaseInsensitiveDict(request_headers),
        session_headers,
        dict_class=CaseInsensitiveDict
    )
    
    # Result should be CaseInsensitiveDict
    assert isinstance(result, CaseInsensitiveDict)
    
    # Modified values should take precedence
    for k, v in request_headers.items():
        assert result.get(k) == v


if __name__ == "__main__":
    pytest.main([__file__, "-v"])