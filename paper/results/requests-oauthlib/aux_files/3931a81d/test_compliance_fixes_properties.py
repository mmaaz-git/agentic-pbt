import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

import json
from unittest.mock import Mock, MagicMock
from urllib.parse import parse_qs, urlparse, urlencode

import pytest
from hypothesis import given, strategies as st, assume, settings

from requests_oauthlib.compliance_fixes import (
    facebook_compliance_fix,
    fitbit_compliance_fix,
    slack_compliance_fix,
    instagram_compliance_fix,
    weibo_compliance_fix,
    mailchimp_compliance_fix,
    plentymarkets_compliance_fix,
    ebay_compliance_fix
)


# Strategy for generating valid JSON objects
json_strategy = st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(min_size=1)
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(
            st.text(min_size=1, max_size=20),
            children,
            max_size=10
        )
    ),
    max_leaves=50
)


# Test 1: JSON round-trip property for fitbit_compliance_fix
@given(
    errors=st.lists(
        st.fixed_dictionaries({
            "errorType": st.text(min_size=1, max_size=20),
            "message": st.text(max_size=50),
        }),
        min_size=1,
        max_size=3
    ),
    other_data=st.dictionaries(
        st.text(min_size=1, max_size=10).filter(lambda s: s != "errors" and s != "error"),
        st.one_of(st.text(max_size=20), st.integers(), st.none()),
        max_size=5
    )
)
@settings(max_examples=100, deadline=None)
def test_fitbit_json_round_trip(errors, other_data):
    """Test that fitbit compliance fix properly transforms errors array to error string"""
    session = Mock()
    hooks = {}
    
    def register_hook(name, func):
        hooks[name] = func
    
    session.register_compliance_hook = register_hook
    fitbit_compliance_fix(session)
    
    # Create response with errors
    response_data = {**other_data, "errors": errors}
    response = Mock()
    response.text = json.dumps(response_data)
    response._content = response.text.encode()
    
    # Apply the compliance fix
    fixed_response = hooks["access_token_response"](response)
    
    # Parse the fixed content
    fixed_data = json.loads(fixed_response._content.decode())
    
    # Properties to verify:
    # 1. The error field should be set to the first error's errorType
    assert "error" in fixed_data
    assert fixed_data["error"] == errors[0]["errorType"]
    
    # 2. All other data should be preserved
    for key, value in other_data.items():
        assert key in fixed_data
        assert fixed_data[key] == value
    
    # 3. The original errors array should still be present
    assert "errors" in fixed_data
    assert fixed_data["errors"] == errors


# Test 2: Facebook compliance fix content-type handling
@given(
    content_type=st.sampled_from([
        "application/json",
        "text/plain",
        "text/html",
        "application/x-www-form-urlencoded",
        None
    ]),
    status_code=st.integers(min_value=100, max_value=599),
    url_params=st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.text(min_size=0, max_size=100),
        max_size=10
    )
)
def test_facebook_content_type_handling(content_type, status_code, url_params):
    """Test that facebook compliance fix properly handles different content types"""
    session = Mock()
    hooks = {}
    
    def register_hook(name, func):
        hooks[name] = func
    
    session.register_compliance_hook = register_hook
    facebook_compliance_fix(session)
    
    response = Mock()
    response.status_code = status_code
    response.headers = {"content-type": content_type} if content_type else {}
    
    # Set up response text as URL-encoded params
    response.text = urlencode(url_params)
    response._content = response.text.encode()
    
    fixed_response = hooks["access_token_response"](response)
    
    # Properties to verify:
    if content_type and "application/json" in content_type:
        # Should not modify JSON responses
        assert fixed_response._content == response.text.encode()
    elif content_type == "text/plain" and status_code == 200:
        # Should convert URL params to JSON
        fixed_data = json.loads(fixed_response._content.decode())
        
        # Check that token_type is added
        assert "token_type" in fixed_data
        assert fixed_data["token_type"] == "Bearer"
        
        # Check expires transformation
        if "expires" in url_params:
            assert "expires_in" in fixed_data
            assert fixed_data["expires_in"] == url_params["expires"]
    else:
        # Should not modify other responses
        assert fixed_response._content == response.text.encode()


# Test 3: Slack URL parameter handling
@given(
    base_url=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='._-'), min_size=1, max_size=20).map(lambda s: f"https://slack.com/api/{s}"),
    existing_params=st.dictionaries(
        st.text(min_size=1, max_size=20).filter(lambda s: s != "token"),
        st.text(min_size=0, max_size=100),
        max_size=5
    ),
    access_token=st.text(min_size=1, max_size=50),
    data_type=st.sampled_from(["dict", "string", "none"])
)
def test_slack_url_parameter_preservation(base_url, existing_params, access_token, data_type):
    """Test that slack compliance fix preserves existing URL parameters"""
    session = Mock()
    session.access_token = access_token
    hooks = {}
    
    def register_hook(name, func):
        hooks[name] = func
    
    session.register_compliance_hook = register_hook
    slack_compliance_fix(session)
    
    # Build URL with existing params
    if existing_params:
        url = base_url + "?" + urlencode(existing_params)
    else:
        url = base_url
    
    headers = {}
    
    # Set up data based on type
    if data_type == "dict":
        data = {"some_key": "some_value"}
    elif data_type == "string":
        data = "some string data"
    else:
        data = None
    
    # Apply the compliance fix
    fixed_url, fixed_headers, fixed_data = hooks["protected_request"](url, headers, data)
    
    # Parse the fixed URL
    parsed_url = urlparse(fixed_url)
    query_params = parse_qs(parsed_url.query, keep_blank_values=True)
    
    # Properties to verify:
    # 1. Token should be added (either in URL or data)
    if data_type == "dict":
        assert fixed_data.get("token") == access_token
    elif data_type == "none":
        assert fixed_data == {"token": access_token}
    else:
        # Token should be in URL for non-dict data
        assert "token" in query_params
        assert access_token in query_params["token"]
    
    # 2. Original parameters should be preserved in URL
    for key, value in existing_params.items():
        assert key in query_params
        assert value in query_params[key]


# Test 4: Weibo JSON manipulation
@given(
    response_data=st.dictionaries(
        st.text(min_size=1, max_size=20).filter(lambda s: s != "token_type"),
        json_strategy,
        max_size=10
    )
)
def test_weibo_token_type_addition(response_data):
    """Test that weibo compliance fix adds token_type field"""
    session = Mock()
    session._client = Mock()
    hooks = {}
    
    def register_hook(name, func):
        hooks[name] = func
    
    session.register_compliance_hook = register_hook
    weibo_compliance_fix(session)
    
    response = Mock()
    response.text = json.dumps(response_data)
    response._content = response.text.encode()
    
    fixed_response = hooks["access_token_response"](response)
    fixed_data = json.loads(fixed_response._content.decode())
    
    # Properties to verify:
    # 1. token_type should be added as "Bearer"
    assert "token_type" in fixed_data
    assert fixed_data["token_type"] == "Bearer"
    
    # 2. All original data should be preserved
    for key, value in response_data.items():
        assert key in fixed_data
        assert fixed_data[key] == value


# Test 5: Instagram URL handling with existing access_token
@given(
    base_url=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='._-/'), min_size=1, max_size=20).map(lambda s: f"https://api.instagram.com/{s}"),
    has_existing_token=st.booleans(),
    existing_token=st.text(min_size=1, max_size=50),
    session_token=st.text(min_size=1, max_size=50),
    other_params=st.dictionaries(
        st.text(min_size=1, max_size=20).filter(lambda s: s != "access_token"),
        st.text(min_size=0, max_size=100),
        max_size=5
    )
)
def test_instagram_existing_token_handling(base_url, has_existing_token, existing_token, 
                                          session_token, other_params):
    """Test that instagram fix respects existing access tokens"""
    session = Mock()
    session.access_token = session_token
    hooks = {}
    
    def register_hook(name, func):
        hooks[name] = func
    
    session.register_compliance_hook = register_hook
    instagram_compliance_fix(session)
    
    # Build URL
    params = dict(other_params)
    if has_existing_token:
        params["access_token"] = existing_token
    
    if params:
        url = base_url + "?" + urlencode(params)
    else:
        url = base_url
    
    headers = {}
    data = None
    
    fixed_url, fixed_headers, fixed_data = hooks["protected_request"](url, headers, data)
    
    parsed_url = urlparse(fixed_url)
    query_params = parse_qs(parsed_url.query, keep_blank_values=True)
    
    # Properties to verify:
    if has_existing_token:
        # Should not modify URL if token already exists
        assert "access_token" in query_params
        assert existing_token in query_params["access_token"]
        # Should not add session token if it's different from existing
        if existing_token != session_token:
            assert session_token not in query_params.get("access_token", [])
    else:
        # Should add session token
        assert "access_token" in query_params
        assert session_token in query_params["access_token"]
    
    # All other params should be preserved
    for key, value in other_params.items():
        assert key in query_params
        assert value in query_params[key]


# Test 6: Idempotence of compliance fixes
@given(
    fix_function=st.sampled_from([
        facebook_compliance_fix,
        fitbit_compliance_fix,
        slack_compliance_fix,
        instagram_compliance_fix,
        weibo_compliance_fix
    ])
)
def test_compliance_fix_idempotence(fix_function):
    """Test that applying compliance fixes multiple times is idempotent"""
    session1 = Mock()
    session1._client = Mock()
    session1.access_token = "test_token"
    hooks1 = {}
    
    def register_hook1(name, func):
        hooks1[name] = func
    
    session1.register_compliance_hook = register_hook1
    
    # Apply once
    result1 = fix_function(session1)
    
    # Apply again
    result2 = fix_function(session1)
    
    # Should return the same session
    assert result1 is session1
    assert result2 is session1
    
    # The hooks dictionary should have the same keys
    # (Note: We can't easily test that the functions are identical,
    # but we can check that the same hooks are registered)
    session2 = Mock()
    session2._client = Mock()
    session2.access_token = "test_token"
    hooks2 = {}
    
    def register_hook2(name, func):
        hooks2[name] = func
    
    session2.register_compliance_hook = register_hook2
    fix_function(session2)
    
    assert set(hooks1.keys()) == set(hooks2.keys())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])