"""Property-based tests for pyramid.security module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings
from unittest.mock import Mock, MagicMock
import warnings

# Suppress deprecation warnings for testing
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    from pyramid.security import (
        AllPermissionsList, ALL_PERMISSIONS,
        Allowed, Denied, PermitsResult,
        LegacySecurityPolicy,
        remember, forget,
        SecurityAPIMixin,
        ISecurityPolicy, IAuthenticationPolicy, IAuthorizationPolicy
    )
    from pyramid.interfaces import ISecurityPolicy as ISP


# Test 1: AllPermissionsList.__contains__ always returns True
@given(st.one_of(
    st.text(),
    st.integers(),
    st.none(),
    st.lists(st.integers()),
    st.tuples(st.text(), st.integers()),
    st.binary(),
    st.floats(allow_nan=True, allow_infinity=True)
))
def test_all_permissions_contains_everything(item):
    """AllPermissionsList should contain any item"""
    apl = AllPermissionsList()
    assert item in apl
    
    # Also test the global instance
    assert item in ALL_PERMISSIONS


# Test 2: AllPermissionsList equality only with same class
@given(
    other=st.one_of(
        st.text(),
        st.integers(),
        st.none(),
        st.lists(st.integers()),
        st.builds(dict),
        st.builds(set),
        st.builds(list)
    )
)
def test_all_permissions_equality(other):
    """AllPermissionsList should only equal other AllPermissionsList instances"""
    apl1 = AllPermissionsList()
    apl2 = AllPermissionsList()
    
    # Should equal other instances of same class
    assert apl1 == apl2
    assert apl1 == ALL_PERMISSIONS
    
    # Should not equal other types
    if not isinstance(other, AllPermissionsList):
        assert apl1 != other


# Test 3: Denied evaluates to False, Allowed evaluates to True
@given(
    msg=st.text(),
    args=st.lists(st.text(), max_size=5)
)
def test_denied_allowed_boolean_behavior(msg, args):
    """Denied should be falsy, Allowed should be truthy"""
    # Create Denied instance
    denied = Denied(msg, *args)
    assert not denied  # Should be falsy
    assert denied == 0  # Should equal 0
    assert bool(denied) is False
    
    # Create Allowed instance
    allowed = Allowed(msg, *args)
    assert allowed  # Should be truthy
    assert allowed == 1  # Should equal 1
    assert bool(allowed) is True


# Test 4: PermitsResult msg property formatting
@given(
    fmt_string=st.from_regex(r'[A-Za-z %s]+', fullmatch=True),
    args=st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=3)
)
def test_permits_result_msg_formatting(fmt_string, args):
    """PermitsResult.msg should format string with args"""
    # Count %s in format string
    fmt_count = fmt_string.count('%s')
    
    # Adjust args to match format string placeholders
    if fmt_count > len(args):
        args = args + [''] * (fmt_count - len(args))
    elif fmt_count < len(args):
        args = args[:fmt_count]
    
    denied = Denied(fmt_string, *args)
    msg = denied.msg
    
    # Should not raise exception
    assert isinstance(msg, str)
    
    # If no args, msg should equal format string
    if not args or fmt_count == 0:
        assert msg == fmt_string


# Test 5: LegacySecurityPolicy.forget() raises ValueError with kwargs
@given(
    kwargs=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.text(),
        min_size=1,
        max_size=5
    )
)
def test_legacy_security_policy_forget_kwargs_error(kwargs):
    """LegacySecurityPolicy.forget() should raise ValueError when given kwargs"""
    policy = LegacySecurityPolicy()
    
    # Create mock request with mock authentication policy
    request = Mock()
    authn_policy = Mock()
    authn_policy.forget = Mock(return_value=[])
    request.registry.getUtility = Mock(return_value=authn_policy)
    
    # Should raise ValueError with any non-empty kwargs
    try:
        result = policy.forget(request, **kwargs)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert 'keyword arguments' in str(e)


# Test 6: LegacySecurityPolicy.forget() works without kwargs
def test_legacy_security_policy_forget_no_kwargs():
    """LegacySecurityPolicy.forget() should work with no kwargs"""
    policy = LegacySecurityPolicy()
    
    # Create mock request with mock authentication policy  
    request = Mock()
    authn_policy = Mock()
    expected_headers = [('Set-Cookie', 'session=deleted')]
    authn_policy.forget = Mock(return_value=expected_headers)
    request.registry.getUtility = Mock(return_value=authn_policy)
    
    # Should not raise and should return headers from authn policy
    result = policy.forget(request)
    assert result == expected_headers
    authn_policy.forget.assert_called_once_with(request)


# Test 7: remember returns empty list when no security policy
@given(
    userid=st.text(),
    kwargs=st.dictionaries(st.text(min_size=1), st.text(), max_size=3)
)
def test_remember_no_policy_returns_empty(userid, kwargs):
    """remember() should return empty list when no security policy exists"""
    # Create request with no security policy
    request = Mock()
    request.registry.queryUtility = Mock(return_value=None)
    
    result = remember(request, userid, **kwargs)
    assert result == []


# Test 8: forget returns empty list when no security policy
@given(
    kwargs=st.dictionaries(st.text(min_size=1), st.text(), max_size=3)
)
def test_forget_no_policy_returns_empty(kwargs):
    """forget() should return empty list when no security policy exists"""
    # Create request with no security policy
    request = Mock()
    request.registry.queryUtility = Mock(return_value=None)
    
    result = forget(request, **kwargs)
    assert result == []


# Test 9: SecurityAPIMixin.is_authenticated property consistency
@given(
    userid=st.one_of(st.none(), st.text(min_size=1), st.integers())
)
def test_security_api_is_authenticated_consistency(userid):
    """is_authenticated should be True iff authenticated_userid is not None"""
    # Create a mock request object with SecurityAPIMixin
    class TestRequest(SecurityAPIMixin):
        def __init__(self):
            self.registry = Mock()
            
    request = TestRequest()
    
    # Mock the security policy
    if userid is None:
        # No user authenticated
        policy = Mock()
        policy.authenticated_userid = Mock(return_value=None)
    else:
        # User is authenticated
        policy = Mock()
        policy.authenticated_userid = Mock(return_value=userid)
    
    request.registry.queryUtility = Mock(return_value=policy)
    
    # Test the consistency
    assert request.is_authenticated == (request.authenticated_userid is not None)
    assert request.is_authenticated == (userid is not None)


# Test 10: SecurityAPIMixin.has_permission with no policy returns Allowed
@given(
    permission=st.text(min_size=1),
    context=st.one_of(st.none(), st.builds(object))
)
def test_security_api_has_permission_no_policy(permission, context):
    """has_permission should return Allowed when no security policy exists"""
    # Create a mock request object with SecurityAPIMixin
    class TestRequest(SecurityAPIMixin):
        def __init__(self):
            self.registry = Mock()
            self.context = Mock()  # Default context
    
    request = TestRequest()
    
    # No security policy
    request.registry.queryUtility = Mock(return_value=None)
    
    result = request.has_permission(permission, context)
    
    # Should return Allowed
    assert isinstance(result, Allowed)
    assert result == True
    assert 'No security policy' in result.msg


# Test 11: Interaction between __eq__ and __contains__ for AllPermissionsList
@given(
    test_item=st.one_of(
        st.just(ALL_PERMISSIONS),
        st.builds(AllPermissionsList)
    )
)
def test_all_permissions_self_containment(test_item):
    """AllPermissionsList instances should contain themselves and equal each other"""
    apl = AllPermissionsList()
    
    # Should contain itself
    assert apl in apl
    assert ALL_PERMISSIONS in apl
    assert apl in ALL_PERMISSIONS
    
    # Should equal other instances
    assert apl == test_item
    assert test_item == apl


if __name__ == "__main__":
    print("Running property-based tests for pyramid.security...")
    
    # Run tests
    test_all_permissions_contains_everything()
    test_all_permissions_equality()
    test_denied_allowed_boolean_behavior()
    test_permits_result_msg_formatting()
    test_legacy_security_policy_forget_kwargs_error()
    test_legacy_security_policy_forget_no_kwargs()
    test_remember_no_policy_returns_empty()
    test_forget_no_policy_returns_empty()
    test_security_api_is_authenticated_consistency()
    test_security_api_has_permission_no_policy()
    test_all_permissions_self_containment()
    
    print("All smoke tests passed!")