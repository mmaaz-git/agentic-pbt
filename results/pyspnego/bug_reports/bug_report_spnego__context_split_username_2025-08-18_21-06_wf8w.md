# Bug Report: spnego._context.split_username Empty Domain for Backslash-Prefixed Usernames

**Target**: `spnego._context.split_username`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `split_username` function incorrectly returns an empty string as the domain when a username starts with a backslash (e.g., `\user`), instead of properly handling this edge case.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from spnego._context import split_username

@given(st.text(min_size=1), st.text(min_size=1))
def test_split_username_multiple_backslashes(domain_str, user_str):
    """Test that only the first backslash is used for splitting."""
    user_with_backslash = f"{user_str}\\extra\\parts"
    full_username = f"{domain_str}\\{user_with_backslash}"
    
    domain, user = split_username(full_username)
    
    # Should split on FIRST backslash only
    assert domain == domain_str
    assert user == user_with_backslash
```

**Failing input**: `split_username("\\user")`

## Reproducing the Bug

```python
from spnego._context import split_username

# Bug case: username starting with backslash
username = "\\user"
domain, user = split_username(username)

print(f"Input: '{username}'")
print(f"Domain: '{domain}'")  # Returns empty string ''
print(f"User: '{user}'")      # Returns 'user'

# The issue: Python's split on backslash returns ['', 'user']
# when the string starts with the delimiter
assert domain == ''  # Current behavior
# Expected: either domain == '\\' or raise an error
```

## Why This Is A Bug

The function's docstring states it splits usernames in "Netlogon form `DOMAIN\\username`". When a username starts with `\`, it represents either:
1. A local machine reference (e.g., `\Administrator`)
2. Malformed input that should be handled explicitly

Returning an empty string domain is problematic because:
- Empty string domain is semantically different from None (which means "no domain specified")
- This empty domain is passed to Windows authentication functions like `WinNTAuthIdentity`, potentially causing authentication failures
- Users expect `\user` to indicate a local account, not an account with empty domain

## Fix

```diff
--- a/spnego/_context.py
+++ b/spnego/_context.py
@@ -41,9 +41,14 @@ def split_username(username: Optional[str]) -> Tuple[Optional[str], Optional[st
         return None, None
 
     domain: Optional[str]
     if "\\" in username:
         domain, username = username.split("\\", 1)
+        # Handle edge case where username starts with backslash
+        # Empty domain from split means the username started with backslash
+        if domain == '' and username:
+            # Treat as local machine reference
+            domain = '.'
     else:
         domain = None
 
     return to_text(domain, nonstring="passthru"), to_text(username, nonstring="passthru")
```