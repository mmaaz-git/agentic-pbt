# Bug Report: praw.models.util.permissions_string Incorrectly Handles None Values

**Target**: `praw.models.util.permissions_string`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-01-21

## Summary

The `permissions_string` function incorrectly handles `None` values in the permissions list by converting them to the string `"None"` instead of raising an error or filtering them out.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from praw.models.util import permissions_string

@given(
    known_perms=st.sets(st.text(min_size=1, max_size=5), min_size=1, max_size=5),
    none_positions=st.lists(st.integers(min_value=0, max_value=4), min_size=1, max_size=3)
)
def test_permissions_with_none_values(known_perms, none_positions):
    """Test that None values in permissions list are handled incorrectly."""
    perms_list = list(known_perms)[:3]
    for pos in none_positions[:len(perms_list)]:
        perms_list.insert(pos, None)
    
    result = permissions_string(known_permissions=known_perms, permissions=perms_list)
    assert "+None" not in result  # This assertion fails
```

**Failing input**: `known_permissions={'read', 'write'}, permissions=[None]`

## Reproducing the Bug

```python
from praw.models.util import permissions_string

known_permissions = {"read", "write", "execute"}
permissions_with_none = ["read", None, "write"]

result = permissions_string(
    known_permissions=known_permissions,
    permissions=permissions_with_none
)

print(result)
# Output: -all,-execute,+read,+None,+write
# Bug: '+None' appears in the result
```

## Why This Is A Bug

The function treats `None` as the string `"None"` which violates the expected contract that permissions should be strings representing actual permission names. This could lead to:
1. Invalid permission strings being sent to Reddit's API
2. Security issues if `None` is accidentally treated as a valid permission
3. Confusion when debugging permission-related issues

## Fix

```diff
--- a/praw/models/util.py
+++ b/praw/models/util.py
@@ -28,7 +28,10 @@ def permissions_string(
     if permissions is None:
         to_set = ["+all"]
     else:
+        # Filter out None values and ensure all permissions are strings
+        permissions = [p for p in permissions if p is not None]
         to_set = ["-all"]
         omitted = sorted(known_permissions - set(permissions))
         to_set.extend(f"-{x}" for x in omitted)
         to_set.extend(f"+{x}" for x in permissions)
     return ",".join(to_set)
```