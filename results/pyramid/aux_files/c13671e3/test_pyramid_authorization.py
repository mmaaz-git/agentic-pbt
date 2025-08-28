#!/usr/bin/env /root/hypothesis-llm/envs/pyramid_env/bin/python3
"""Property-based tests for pyramid.authorization module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from pyramid.authorization import (
    ACLHelper, Allow, Deny, Everyone, Authenticated,
    ACLAllowed, ACLDenied, ALL_PERMISSIONS
)
import random
import string


# Strategy for generating principal names
principal_strategy = st.one_of(
    st.just(Everyone),
    st.just(Authenticated),
    st.text(min_size=1, max_size=20, alphabet=string.ascii_letters + string.digits + "_-")
)

# Strategy for generating permission names
permission_strategy = st.one_of(
    st.just(ALL_PERMISSIONS),
    st.text(min_size=1, max_size=20, alphabet=string.ascii_letters + string.digits + "_-")
)

# Strategy for generating ACE actions
ace_action_strategy = st.sampled_from([Allow, Deny])

# Strategy for generating a single ACE (Access Control Entry)
def ace_strategy():
    return st.tuples(
        ace_action_strategy,
        principal_strategy,
        st.one_of(
            permission_strategy,  # Single permission
            st.lists(permission_strategy, min_size=1, max_size=5)  # List of permissions
        )
    )

# Strategy for generating ACLs (Access Control Lists)
acl_strategy = st.lists(ace_strategy(), min_size=0, max_size=10)


class MockContext:
    """Mock context object with optional ACL and parent"""
    def __init__(self, acl=None, parent=None, make_callable=False):
        if acl is not None:
            if make_callable:
                self.__acl__ = lambda: acl
            else:
                self.__acl__ = acl
        self.__parent__ = parent


# Property 1: Default Deny - if no ACL or no matching ACE, must return ACLDenied
@given(
    principals=st.lists(principal_strategy, min_size=1, max_size=5),
    permission=permission_strategy
)
def test_default_deny_no_acl(principals, permission):
    """Test that permits() returns ACLDenied when no ACL exists"""
    helper = ACLHelper()
    context = MockContext()  # No ACL
    
    result = helper.permits(context, principals, permission)
    
    assert isinstance(result, ACLDenied)
    assert result == False  # ACLDenied evaluates to False


@given(
    principals=st.lists(principal_strategy, min_size=1, max_size=5),
    permission=permission_strategy,
    acl=acl_strategy
)
def test_default_deny_no_match(principals, permission, acl):
    """Test that permits() returns ACLDenied when no ACE matches"""
    # Ensure no ACE in the ACL matches our principals and permission
    filtered_acl = []
    for ace in acl:
        action, principal, perms = ace
        # Keep ACE only if it doesn't match our test case
        if principal not in principals:
            filtered_acl.append(ace)
        elif isinstance(perms, list) and permission not in perms:
            filtered_acl.append(ace)
        elif not isinstance(perms, list) and permission != perms:
            filtered_acl.append(ace)
    
    helper = ACLHelper()
    context = MockContext(acl=filtered_acl)
    
    result = helper.permits(context, principals, permission)
    
    assert isinstance(result, ACLDenied)
    

# Property 2: Deny overrides Allow in permits()
@given(
    principal=principal_strategy,
    permission=permission_strategy,
    other_aces=st.lists(ace_strategy(), min_size=0, max_size=5)
)
def test_deny_overrides_allow(principal, permission, other_aces):
    """Test that Deny ACE stops processing even if Allow exists later"""
    # Create an ACL with Deny first, then Allow
    deny_ace = (Deny, principal, permission)
    allow_ace = (Allow, principal, permission)
    
    # Place deny before allow
    acl = [deny_ace] + other_aces + [allow_ace]
    
    helper = ACLHelper()
    context = MockContext(acl=acl)
    
    result = helper.permits(context, [principal], permission)
    
    assert isinstance(result, ACLDenied)
    assert result == False


# Property 3: Everyone Deny clears all in principals_allowed_by_permission
@given(
    permission=permission_strategy,
    allowed_principals=st.lists(principal_strategy, min_size=1, max_size=5),
    denied_principals=st.lists(principal_strategy, min_size=0, max_size=3)
)
def test_everyone_deny_clears_all(permission, allowed_principals, denied_principals):
    """Test that Deny Everyone clears all previously allowed principals"""
    # Create parent context with some Allow ACEs
    parent_acl = [(Allow, p, permission) for p in allowed_principals]
    parent = MockContext(acl=parent_acl)
    
    # Create child context with Deny Everyone
    child_acl = [(Deny, Everyone, permission)]
    # Add some more allows after the deny to ensure they still work
    child_acl.extend([(Allow, p, permission) for p in denied_principals])
    child = MockContext(acl=child_acl, parent=parent)
    
    helper = ACLHelper()
    result = helper.principals_allowed_by_permission(child, permission)
    
    # After Deny Everyone, only principals allowed after that point should be in result
    assert Everyone not in result  # Everyone itself shouldn't be in the allowed set
    for p in allowed_principals:
        if p not in denied_principals:
            assert p not in result  # Previously allowed should be cleared
    

# Property 4: Consistency between permits and principals_allowed_by_permission
@given(
    permission=permission_strategy,
    acl=acl_strategy
)
@settings(max_examples=200)
def test_consistency_permits_and_principals_allowed(permission, acl):
    """Test that principals in principals_allowed_by_permission get ACLAllowed from permits"""
    helper = ACLHelper()
    context = MockContext(acl=acl)
    
    # Get all principals allowed for this permission
    allowed_principals = helper.principals_allowed_by_permission(context, permission)
    
    # For each allowed principal, permits should return ACLAllowed
    # (unless there's a Deny that takes precedence in permits logic)
    for principal in allowed_principals:
        result = helper.permits(context, [principal], permission)
        
        # Check if there's a Deny ACE that would override
        has_deny = False
        for ace in acl:
            action, ace_principal, ace_perms = ace
            if action == Deny and ace_principal == principal:
                if not isinstance(ace_perms, list):
                    ace_perms = [ace_perms]
                if permission in ace_perms:
                    has_deny = True
                    break
        
        if not has_deny:
            # If no explicit deny, the principal should be allowed
            assert isinstance(result, ACLAllowed), f"Principal {principal} in allowed list but permits returned {result}"


# Property 5: Callable ACL support
@given(
    principals=st.lists(principal_strategy, min_size=1, max_size=5),
    permission=permission_strategy,
    acl=acl_strategy,
    use_callable=st.booleans()
)
def test_callable_acl_support(principals, permission, acl, use_callable):
    """Test that callable ACLs work the same as regular ACLs"""
    helper = ACLHelper()
    
    # Create two contexts, one with regular ACL, one with callable
    context_regular = MockContext(acl=acl, make_callable=False)
    context_callable = MockContext(acl=acl, make_callable=use_callable)
    
    # Both should give the same result
    result_regular = helper.permits(context_regular, principals, permission)
    result_callable = helper.permits(context_callable, principals, permission)
    
    assert type(result_regular) == type(result_callable)
    assert result_regular == result_callable
    
    # Also test principals_allowed_by_permission
    allowed_regular = helper.principals_allowed_by_permission(context_regular, permission)
    allowed_callable = helper.principals_allowed_by_permission(context_callable, permission)
    
    assert allowed_regular == allowed_callable


# Property 6: Permission list handling
@given(
    principal=principal_strategy,
    permissions=st.lists(permission_strategy, min_size=2, max_size=5, unique=True),
    other_principals=st.lists(principal_strategy, min_size=0, max_size=3)
)
def test_permission_list_handling(principal, permissions, other_principals):
    """Test that ACEs with permission lists work correctly"""
    assume(len(permissions) >= 2)
    
    # Create ACL with permission list
    acl = [(Allow, principal, permissions)]  # Allow principal for all permissions in list
    
    helper = ACLHelper()
    context = MockContext(acl=acl)
    
    # Each permission in the list should be allowed
    for perm in permissions:
        result = helper.permits(context, [principal], perm)
        assert isinstance(result, ACLAllowed), f"Permission {perm} should be allowed"
    
    # A permission not in the list should be denied
    unique_perm = "unique_permission_xyz_" + ''.join(random.choices(string.ascii_lowercase, k=5))
    assume(unique_perm not in permissions)
    result = helper.permits(context, [principal], unique_perm)
    assert isinstance(result, ACLDenied), f"Permission {unique_perm} should be denied"


if __name__ == "__main__":
    # Run the tests
    import pytest
    pytest.main([__file__, "-v"])