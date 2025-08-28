#!/usr/bin/env /root/hypothesis-llm/envs/pyramid_env/bin/python3
"""Investigate the Everyone principal behavior in principals_allowed_by_permission"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.authorization import (
    ACLHelper, Allow, Deny, Everyone
)


class MockContext:
    def __init__(self, acl=None, parent=None):
        if acl is not None:
            self.__acl__ = acl
        self.__parent__ = parent


def test_everyone_deny_after_allow():
    """Test Everyone behavior when both Allow and Deny exist"""
    helper = ACLHelper()
    
    # Case 1: Allow Everyone, then Deny Everyone for same permission
    acl1 = [
        (Allow, Everyone, 'read'),
        (Deny, Everyone, 'read')
    ]
    context1 = MockContext(acl=acl1)
    
    # Case 2: Deny Everyone, then Allow Everyone for same permission  
    acl2 = [
        (Deny, Everyone, 'read'),
        (Allow, Everyone, 'read')
    ]
    context2 = MockContext(acl=acl2)
    
    # Test permits() - should respect order
    result1_permits = helper.permits(context1, [Everyone], 'read')
    result2_permits = helper.permits(context2, [Everyone], 'read')
    
    print(f"ACL: Allow then Deny")
    print(f"  permits([Everyone], 'read'): {result1_permits} (type: {type(result1_permits).__name__})")
    
    print(f"\nACL: Deny then Allow")
    print(f"  permits([Everyone], 'read'): {result2_permits} (type: {type(result2_permits).__name__})")
    
    # Test principals_allowed_by_permission
    allowed1 = helper.principals_allowed_by_permission(context1, 'read')
    allowed2 = helper.principals_allowed_by_permission(context2, 'read')
    
    print(f"\nACL: Allow then Deny")
    print(f"  principals_allowed_by_permission: {allowed1}")
    print(f"  Is Everyone in allowed set? {Everyone in allowed1}")
    
    print(f"\nACL: Deny then Allow")  
    print(f"  principals_allowed_by_permission: {allowed2}")
    print(f"  Is Everyone in allowed set? {Everyone in allowed2}")
    
    # According to the docstring for principals_allowed_by_permission:
    # "if later in the walking process that principal is mentioned in any 
    # Deny ACE for the permission, the principal is removed from the allow list"
    #
    # "If a Deny to the principal Everyone is encountered during the
    # walking process that matches the permission, the allow list is
    # cleared for all principals encountered in previous ACLs."
    
    print("\n" + "="*60)
    print("Analysis of potential bug:")
    print("="*60)
    
    if Everyone in allowed1:
        print("\nPOTENTIAL BUG FOUND!")
        print("In Case 1 (Allow then Deny), Everyone is in the allowed set.")
        print("According to the docstring, when a Deny for Everyone is encountered,")
        print("it should clear the allow list for all principals.")
        print("\nThe code at line 199-203 in authorization.py handles Deny + Everyone:")
        print("  if ace_principal == Everyone:")
        print("      # clear the entire allowed set")
        print("      allowed = set()")
        print("      break")
        print("\nBut this only clears previously accumulated principals,")
        print("not the ones being added in the current ACL iteration!")
    
    print("\n" + "="*60)
    print("Testing with parent-child context hierarchy:")
    print("="*60)
    
    # Test with parent-child relationship
    parent = MockContext(acl=[(Allow, Everyone, 'read')])
    child = MockContext(acl=[(Deny, Everyone, 'read')], parent=parent)
    
    allowed_child = helper.principals_allowed_by_permission(child, 'read')
    print(f"\nParent ACL: [(Allow, Everyone, 'read')]")
    print(f"Child ACL: [(Deny, Everyone, 'read')]")
    print(f"principals_allowed_by_permission on child: {allowed_child}")
    print(f"Is Everyone in allowed set? {Everyone in allowed_child}")
    
    if Everyone in allowed_child:
        print("\nThis seems wrong! The child's Deny should override parent's Allow.")


if __name__ == "__main__":
    test_everyone_deny_after_allow()