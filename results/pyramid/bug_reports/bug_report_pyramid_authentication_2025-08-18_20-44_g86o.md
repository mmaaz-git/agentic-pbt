# Bug Report: pyramid.authentication Empty Tokens List Round-Trip Failure

**Target**: `pyramid.authentication.AuthTicket` and `parse_ticket`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

When an empty tokens list is passed to AuthTicket and then parsed back using parse_ticket, it returns `['']` instead of `[]`, breaking the round-trip property and causing incorrect boolean evaluation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyramid.authentication import AuthTicket, parse_ticket

@given(
    secret=st.text(min_size=1),
    userid=st.text(min_size=1),
    ip=st.from_regex(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$').filter(
        lambda x: all(int(p) <= 255 for p in x.split('.'))
    ),
    tokens=st.lists(st.from_regex(r'^[A-Za-z][A-Za-z0-9+_-]*$'), max_size=5),
    hashalg=st.sampled_from(['md5', 'sha256'])
)
def test_auth_ticket_tokens_round_trip(secret, userid, ip, tokens, hashalg):
    """Test that tokens list round-trips correctly"""
    ticket = AuthTicket(secret, userid, ip, tokens=tokens, hashalg=hashalg)
    cookie = ticket.cookie_value()
    _, _, parsed_tokens, _ = parse_ticket(secret, cookie, ip, hashalg)
    assert list(tokens) == parsed_tokens
```

**Failing input**: `tokens=[]`

## Reproducing the Bug

```python
from pyramid.authentication import AuthTicket, parse_ticket

ticket = AuthTicket(
    secret='secret',
    userid='testuser',
    ip='127.0.0.1',
    tokens=[],  # Empty list
    hashalg='md5'
)

cookie_value = ticket.cookie_value()
timestamp, userid, parsed_tokens, user_data = parse_ticket(
    secret='secret',
    ticket=cookie_value,
    ip='127.0.0.1',
    hashalg='md5'
)

print(f"Original tokens: {[]}")
print(f"Parsed tokens:   {parsed_tokens}")
print(f"Are equal: {[] == parsed_tokens}")
print(f"bool([]): {bool([])}")
print(f"bool(parsed_tokens): {bool(parsed_tokens)}")
```

## Why This Is A Bug

The round-trip property of serialization is violated. An empty tokens list `[]` becomes `['']` after serialization and parsing. This changes the boolean value from `False` to `True`, potentially breaking application logic that checks `if tokens:` to determine if any tokens are present.

## Fix

```diff
--- a/pyramid/authentication.py
+++ b/pyramid/authentication.py
@@ -775,7 +775,10 @@ def parse_ticket(secret, ticket, ip, hashalg='md5'):
             'Digest signature is not correct', expected=(expected, digest)
         )
 
-    tokens = tokens.split(',')
+    if tokens:
+        tokens = tokens.split(',')
+    else:
+        tokens = []
 
     return (timestamp, userid, tokens, user_data)
```