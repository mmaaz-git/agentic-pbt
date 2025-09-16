# Bug Report: requests.adapters.get_auth_from_url Fails on Username-Only URLs

**Target**: `requests.adapters.get_auth_from_url`
**Severity**: Medium  
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

get_auth_from_url incorrectly returns empty strings for both username and password when a URL contains only a username (no password), losing valid authentication data.

## Property-Based Test

```python
@given(
    st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_characters='/@:[]')),
    st.text(min_size=0, max_size=20, alphabet=st.characters(blacklist_characters='/@:[]'))
)
def test_auth_extraction_from_constructed_url(username, password):
    """
    Property: If we construct a URL with known auth components,
    get_auth_from_url should extract them correctly (accounting for URL encoding).
    """
    if password:
        url = f"http://{quote(username, safe='')}:{quote(password, safe='')}@example.com/path"
    else:
        url = f"http://{quote(username, safe='')}@example.com/path"
    
    extracted_user, extracted_pass = get_auth_from_url(url)
    
    assert extracted_user == username
    if password:
        assert extracted_pass == password
    else:
        assert extracted_pass == ""
```

**Failing input**: `username='0', password=''`

## Reproducing the Bug

```python
from requests.adapters import get_auth_from_url

# URLs with username but no password
test_urls = [
    'http://user@example.com',
    'http://admin@localhost:8080/path',
    'https://0@api.example.com',
]

for url in test_urls:
    username, password = get_auth_from_url(url)
    print(f"URL: {url}")
    print(f"  Expected: username='{url.split('@')[0].split('//')[-1]}', password=''")
    print(f"  Got: username='{username}', password='{password}'")
```

## Why This Is A Bug

URLs can legitimately contain just a username without a password (e.g., `http://user@example.com`). The function should extract the username and return an empty string for the password. Instead, it returns empty strings for both, completely losing the authentication information. This breaks authentication for services that use username-only auth or where passwords are provided through other means.

## Fix

```diff
--- a/requests/utils.py
+++ b/requests/utils.py
@@ -914,7 +914,10 @@ def get_auth_from_url(url):
     parsed = urlparse(url)
 
     try:
-        auth = (unquote(parsed.username), unquote(parsed.password))
+        username = unquote(parsed.username) if parsed.username else ""
+        password = unquote(parsed.password) if parsed.password else ""
+        auth = (username, password)
     except (AttributeError, TypeError):
         auth = ("", "")
 
     return auth
```

The fix checks if username and password are None before calling unquote, preventing the TypeError that causes the function to return empty strings for both values.