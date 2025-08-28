# Bug Report: pyramid.request Unicode Encoding Error in call_app_with_subpath_as_path_info

**Target**: `pyramid.request.call_app_with_subpath_as_path_info`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `call_app_with_subpath_as_path_info` function crashes with a `UnicodeEncodeError` when the request's subpath contains Unicode characters that cannot be encoded to latin-1 (characters with code points > 255).

## Property-Based Test

```python
from hypothesis import given, strategies as st
from unittest.mock import Mock
from pyramid.request import call_app_with_subpath_as_path_info

@given(st.lists(st.text(alphabet="€£¥🦄💀😈", min_size=1), min_size=1, max_size=3))
def test_unicode_in_subpath(subpath_elements):
    request = Mock()
    request.subpath = subpath_elements
    request.environ = {'SCRIPT_NAME': '', 'PATH_INFO': '/' + '/'.join(subpath_elements)}
    
    new_request = Mock()
    new_request.environ = {}
    new_request.get_response = Mock(return_value="response")
    request.copy = Mock(return_value=new_request)
    
    app = Mock()
    
    # This crashes with UnicodeEncodeError
    result = call_app_with_subpath_as_path_info(request, app)
```

**Failing input**: `['€']` (Euro sign, U+20AC)

## Reproducing the Bug

```python
from unittest.mock import Mock
from pyramid.request import call_app_with_subpath_as_path_info

request = Mock()
request.subpath = ['€', 'page']
request.environ = {'SCRIPT_NAME': '', 'PATH_INFO': '/€/page'}

new_request = Mock()
new_request.environ = {}
new_request.get_response = Mock(return_value="response")
request.copy = Mock(return_value=new_request)

app = Mock()

# Raises: UnicodeEncodeError: 'latin-1' codec can't encode character '\u20ac' in position 0
call_app_with_subpath_as_path_info(request, app)
```

## Why This Is A Bug

The function is designed to handle WSGI request path manipulation, and WSGI environments can contain Unicode characters. The bug occurs in the workback logic (line 301 of pyramid/request.py) where the function attempts to encode path elements to latin-1:

```python
tmp.insert(0, text_(bytes_(el, 'latin-1'), 'utf-8'))
```

When `el` contains characters outside the latin-1 range (like emojis, currency symbols beyond £, or extended Unicode), the `bytes_(el, 'latin-1')` call fails. This makes the function incompatible with internationalized web applications that use Unicode URLs.

## Fix

```diff
--- a/pyramid/request.py
+++ b/pyramid/request.py
@@ -298,7 +298,11 @@ def call_app_with_subpath_as_path_info(request, app):
             break
         el = workback.pop()
         if el:
-            tmp.insert(0, text_(bytes_(el, 'latin-1'), 'utf-8'))
+            try:
+                tmp.insert(0, text_(bytes_(el, 'latin-1'), 'utf-8'))
+            except UnicodeEncodeError:
+                # For characters outside latin-1, keep them as-is
+                tmp.insert(0, el)
 
     # strip all trailing slashes from workback to avoid appending undue slashes
     # to end of script_name
```

Alternatively, the encoding strategy could be reconsidered to use UTF-8 throughout instead of the UTF-8/latin-1 mix.