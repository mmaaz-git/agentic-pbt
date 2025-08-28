# Bug Report: pyramid.authorization ACL Processing Logic Error

**Target**: `pyramid.authorization.ACLHelper.principals_allowed_by_permission`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-01-18

## Summary

The `principals_allowed_by_permission` method incorrectly includes `Everyone` in the allowed principals set when an ACL contains both `Allow Everyone` and `Deny Everyone` for the same permission (with Allow appearing first).

## Property-Based Test

```python
@given(
    principal=principal_strategy,
    permission=simple_permission_strategy,
    insert_position=st.integers(min_value=0, max_value=5)
)
def test_acl_ordering_matters(principal, permission, insert_position):
    """Test that ACL order matters for permits() but not principals_allowed_by_permission"""
    allow_ace = (Allow, principal, permission)
    deny_ace = (Deny, principal, permission)
    other_aces = [(Allow, "other", "other_perm") for _ in range(insert_position)]
    
    acl_allow_first = other_aces + [allow_ace, deny_ace]
    
    helper = ACLHelper()
    context_allow_first = MockContext(acl=acl_allow_first)
    
    allowed_allow_first = helper.principals_allowed_by_permission(context_allow_first, permission)
    
    # Both should not have the principal since there's a Deny
    assert principal not in allowed_allow_first
```

**Failing input**: `principal='system.Everyone', permission='0', insert_position=0`

## Reproducing the Bug

```python
from pyramid.authorization import ACLHelper, Allow, Deny, Everyone

class MockContext:
    def __init__(self, acl=None):
        if acl is not None:
            self.__acl__ = acl

helper = ACLHelper()

acl = [
    (Allow, Everyone, 'read'),
    (Deny, Everyone, 'read')
]
context = MockContext(acl=acl)

allowed = helper.principals_allowed_by_permission(context, 'read')
print(f"Allowed principals: {allowed}")
print(f"Is Everyone allowed? {Everyone in allowed}")
# Output: Is Everyone allowed? True (INCORRECT - should be False)
```

## Why This Is A Bug

According to the method's docstring: "If a Deny to the principal Everyone is encountered during the walking process that matches the permission, the allow list is cleared for all principals encountered in previous ACLs."

The current implementation clears the accumulated `allowed` set when encountering `Deny Everyone`, but then incorrectly adds back principals from `allowed_here` after the loop. This violates the documented behavior that `Deny Everyone` should clear ALL principals.

## Fix

```diff
--- a/pyramid/authorization.py
+++ b/pyramid/authorization.py
@@ -184,6 +184,7 @@ class ACLHelper:
 
             allowed_here = set()
             denied_here = set()
+            everyone_denied = False
 
             if acl and callable(acl):
                 acl = acl()
@@ -200,10 +201,12 @@ class ACLHelper:
                         # clear the entire allowed set, as we've hit a
                         # deny of Everyone ala (Deny, Everyone, ALL)
                         allowed = set()
+                        everyone_denied = True
                         break
                     elif ace_principal in allowed:
                         allowed.remove(ace_principal)
 
-            allowed.update(allowed_here)
+            if not everyone_denied:
+                allowed.update(allowed_here)
 
         return allowed
```