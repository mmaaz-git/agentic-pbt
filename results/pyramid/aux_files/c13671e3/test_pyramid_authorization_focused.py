#!/usr/bin/env /root/hypothesis-llm/envs/pyramid_env/bin/python3
"""Focused property-based tests for pyramid.authorization edge cases"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from pyramid.authorization import (
    ACLHelper, Allow, Deny, Everyone, Authenticated,
    ACLAllowed, ACLDenied, ALL_PERMISSIONS
)
import string


# Strategy for generating principal names
principal_strategy = st.one_of(
    st.just(Everyone),
    st.just(Authenticated),
    st.text(min_size=1, max_size=20, alphabet=string.ascii_letters + string.digits + "_-")
)

# Strategy for generating permission names (without ALL_PERMISSIONS for some tests)
simple_permission_strategy = st.text(min_size=1, max_size=20, alphabet=string.ascii_letters + string.digits + "_-")


class MockContext:
    """Mock context object with optional ACL and parent"""
    def __init__(self, acl=None, parent=None, make_callable=False):
        if acl is not None:
            if make_callable:
                self.__acl__ = lambda: acl
            else:
                self.__acl__ = acl
        self.__parent__ = parent


# Test for potential bug in principals_allowed_by_permission with duplicate principals
@given(
    permission=simple_permission_strategy,
    principal=principal_strategy
)
def test_duplicate_principals_in_lineage(permission, principal):
    """Test handling of duplicate Allow ACEs for same principal in lineage"""
    # Create parent with Allow for principal
    parent_acl = [(Allow, principal, permission)]
    parent = MockContext(acl=parent_acl)
    
    # Create child with another Allow for same principal
    child_acl = [(Allow, principal, permission)]
    child = MockContext(acl=child_acl, parent=parent)
    
    helper = ACLHelper()
    allowed = helper.principals_allowed_by_permission(child, permission)
    
    # Principal should appear only once in the set
    assert isinstance(allowed, set)
    principal_count = sum(1 for p in allowed if p == principal)
    assert principal_count <= 1, f"Principal {principal} appears {principal_count} times in set"


# Test interaction between ALL_PERMISSIONS and specific denies
@given(
    principal=principal_strategy,
    specific_permission=simple_permission_strategy
)
def test_all_permissions_with_specific_deny(principal, specific_permission):
    """Test that Allow ALL_PERMISSIONS can be overridden by specific Deny"""
    # ACL: Allow ALL_PERMISSIONS, then Deny specific permission
    acl = [
        (Allow, principal, ALL_PERMISSIONS),
        (Deny, principal, specific_permission)
    ]
    
    helper = ACLHelper()
    context = MockContext(acl=acl)
    
    # The Deny should come after Allow in the ACL traversal for permits()
    result = helper.permits(context, [principal], specific_permission)
    
    # Since permits() stops at first match, the Allow ALL_PERMISSIONS should match first
    assert isinstance(result, ACLAllowed), "Allow ALL_PERMISSIONS should match before Deny"


# Test edge case: Empty principal list
@given(
    permission=simple_permission_strategy,
    acl=st.lists(
        st.tuples(
            st.sampled_from([Allow, Deny]),
            principal_strategy,
            simple_permission_strategy
        ),
        min_size=1,
        max_size=5
    )
)
def test_empty_principals_list(permission, acl):
    """Test behavior with empty principals list"""
    helper = ACLHelper()
    context = MockContext(acl=acl)
    
    # Empty principals list should always result in deny
    result = helper.permits(context, [], permission)
    assert isinstance(result, ACLDenied), "Empty principals should be denied"


# Test potential confusion between Everyone and specific principals in principals_allowed
@given(
    permission=simple_permission_strategy,
    specific_principals=st.lists(
        st.text(min_size=1, max_size=10, alphabet=string.ascii_letters),
        min_size=1,
        max_size=3,
        unique=True
    )
)
def test_everyone_vs_specific_principals(permission, specific_principals):
    """Test that Everyone doesn't get confused with specific principals"""
    # Create ACL with mixed Everyone and specific principals
    acl = [(Allow, Everyone, permission)]
    for p in specific_principals:
        acl.append((Deny, p, permission))
    
    helper = ACLHelper()
    context = MockContext(acl=acl)
    
    allowed = helper.principals_allowed_by_permission(context, permission)
    
    # Everyone should be in allowed set
    assert Everyone in allowed, "Everyone should be allowed"
    
    # Specific denied principals should not be in allowed set
    for p in specific_principals:
        assert p not in allowed, f"Denied principal {p} should not be allowed"


# Test ACL ordering effects
@given(
    principal=principal_strategy,
    permission=simple_permission_strategy,
    insert_position=st.integers(min_value=0, max_value=5)
)
def test_acl_ordering_matters(principal, permission, insert_position):
    """Test that ACL order matters for permits() but not principals_allowed_by_permission"""
    # Create two ACLs with same ACEs but different order
    allow_ace = (Allow, principal, permission)
    deny_ace = (Deny, principal, permission)
    other_aces = [(Allow, "other", "other_perm") for _ in range(insert_position)]
    
    acl_allow_first = other_aces + [allow_ace, deny_ace]
    acl_deny_first = other_aces + [deny_ace, allow_ace]
    
    helper = ACLHelper()
    context_allow_first = MockContext(acl=acl_allow_first)
    context_deny_first = MockContext(acl=acl_deny_first)
    
    # permits() should give different results based on order
    result_allow_first = helper.permits(context_allow_first, [principal], permission)
    result_deny_first = helper.permits(context_deny_first, [principal], permission)
    
    assert isinstance(result_allow_first, ACLAllowed), "Allow first should succeed"
    assert isinstance(result_deny_first, ACLDenied), "Deny first should fail"
    
    # principals_allowed_by_permission processes differently (walks up from root)
    # It should show the principal as denied in both cases since there's a Deny
    allowed_allow_first = helper.principals_allowed_by_permission(context_allow_first, permission)
    allowed_deny_first = helper.principals_allowed_by_permission(context_deny_first, permission)
    
    # Both should not have the principal since there's a Deny
    assert principal not in allowed_allow_first
    assert principal not in allowed_deny_first


# Test potential issue with None values
@given(
    permission=simple_permission_strategy
)
def test_none_handling(permission):
    """Test that None in various positions is handled correctly"""
    helper = ACLHelper()
    
    # Context with no parent (None parent is normal)
    context = MockContext(acl=[(Allow, Everyone, permission)], parent=None)
    result = helper.permits(context, [Everyone], permission)
    assert isinstance(result, ACLAllowed)
    
    # Context that returns None for __acl__ (should be skipped)
    context_none_acl = MockContext(acl=None)
    result = helper.permits(context_none_acl, [Everyone], permission)
    assert isinstance(result, ACLDenied), "None ACL should result in deny"


# Test recursive parent chains
@given(
    permission=simple_permission_strategy,
    chain_length=st.integers(min_value=1, max_value=10)
)
def test_deep_lineage(permission, chain_length):
    """Test behavior with deep parent chains"""
    # Create a chain of contexts
    root = MockContext(acl=[(Deny, Everyone, permission)])
    current = root
    
    for i in range(chain_length):
        # Alternate between Allow and Deny
        action = Allow if i % 2 == 0 else Deny
        child = MockContext(
            acl=[(action, f"principal_{i}", permission)],
            parent=current
        )
        current = child
    
    helper = ACLHelper()
    
    # Test permits for the last principal
    last_principal = f"principal_{chain_length - 1}"
    result = helper.permits(current, [last_principal], permission)
    
    # The result should depend on whether the last ACE was Allow or Deny
    if (chain_length - 1) % 2 == 0:
        assert isinstance(result, ACLAllowed)
    else:
        assert isinstance(result, ACLDenied)
    
    # Everyone should always be denied (from root)
    result_everyone = helper.permits(current, [Everyone], permission)
    assert isinstance(result_everyone, ACLDenied)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])