# Bug Report: UserCache Bidirectional Map Inconsistency

**Target**: `pyatlan.cache.user_cache.UserCache`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

UserCache's bidirectional maps become inconsistent when multiple user IDs have the same username or email, silently overwriting previous mappings and breaking cache integrity.

## Property-Based Test

```python
@given(
    st.dictionaries(
        keys=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        values=st.tuples(
            st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
            st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and '@' not in x)
            .map(lambda x: f"{x}@example.com")
        ),
        min_size=0,
        max_size=20
    )
)
def test_user_cache_bidirectional_consistency(user_data: Dict[str, tuple]):
    """Test that UserCache maintains bidirectional map consistency."""
    cache = UserCache(Mock())
    
    for user_id, (username, email) in user_data.items():
        cache.map_id_to_name[user_id] = username
        cache.map_name_to_id[username] = user_id
        cache.map_email_to_id[email] = user_id
    
    # Property: id->name and name->id should be consistent
    for user_id, username in cache.map_id_to_name.items():
        if username in cache.map_name_to_id:
            assert cache.map_name_to_id[username] == user_id
```

**Failing input**: `{'0': ('0', '0@example.com'), '00': ('0', '0@example.com')}`

## Reproducing the Bug

```python
import sys
from unittest.mock import Mock
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from pyatlan.cache.user_cache import UserCache

mock_client = Mock()
mock_client.token = Mock()
mock_client.token.get_by_id = Mock(return_value=None)

cache = UserCache(mock_client)

cache.map_id_to_name["user-id-1"] = "john.doe"
cache.map_name_to_id["john.doe"] = "user-id-1"

cache.map_id_to_name["user-id-2"] = "john.doe"
cache.map_name_to_id["john.doe"] = "user-id-2"

print(f"map_id_to_name['user-id-1'] = '{cache.map_id_to_name['user-id-1']}'")
print(f"map_id_to_name['user-id-2'] = '{cache.map_id_to_name['user-id-2']}'")
print(f"map_name_to_id['john.doe'] = '{cache.map_name_to_id['john.doe']}'")
print("Bug: user-id-1 is no longer accessible by name!")

retrieved_id = cache.map_name_to_id.get("john.doe")
print(f"Looking up 'john.doe' returns: {retrieved_id}")
print("Expected: Could be either user-id-1 or user-id-2, or an error")
print("Actual: Only returns user-id-2, user-id-1 is lost")
```

## Why This Is A Bug

The cache's bidirectional maps assume usernames and emails are unique across all users. When the `_refresh_cache` method encounters duplicate usernames or emails, it silently overwrites the previous mapping. This breaks the bidirectional consistency invariant - multiple user IDs can map to the same username, but the reverse mapping can only store one. This could lead to:
1. Wrong user being retrieved from cache
2. Permission/authorization issues if the wrong user's credentials are used
3. Data loss as some users become unreachable via name/email lookup

## Fix

```diff
--- a/pyatlan/cache/user_cache.py
+++ b/pyatlan/cache/user_cache.py
@@ -64,17 +64,25 @@ class UserCache:
     def _refresh_cache(self) -> None:
         with self.lock:
             users = self.client.user.get_all()
             if not users:
                 return
             self.map_id_to_name = {}
             self.map_name_to_id = {}
             self.map_email_to_id = {}
             for user in users:
                 user_id = str(user.id)
                 username = str(user.username)
                 user_email = str(user.email)
+                
+                # Check for duplicate username
+                if username in self.map_name_to_id:
+                    raise ValueError(f"Duplicate username '{username}' found for users {self.map_name_to_id[username]} and {user_id}")
+                
+                # Check for duplicate email
+                if user_email in self.map_email_to_id:
+                    raise ValueError(f"Duplicate email '{user_email}' found for users {self.map_email_to_id[user_email]} and {user_id}")
+                
                 self.map_id_to_name[user_id] = username
                 self.map_name_to_id[username] = user_id
                 self.map_email_to_id[user_email] = user_id
```