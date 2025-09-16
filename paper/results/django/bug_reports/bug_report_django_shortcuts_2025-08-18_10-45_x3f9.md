# Bug Report: django.shortcuts resolve_url Returns None When get_absolute_url Returns None

**Target**: `django.shortcuts.resolve_url`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

When an object's `get_absolute_url()` method returns `None`, `resolve_url()` passes it through unchanged, causing `redirect()` to create a Location header with the literal string "None".

## Property-Based Test

```python
from hypothesis import given, strategies as st
from django.shortcuts import resolve_url, redirect

class ModelWithGetAbsoluteUrl:
    def __init__(self, return_value):
        self.return_value = return_value
    
    def get_absolute_url(self):
        return self.return_value

@given(st.none())
def test_resolve_url_with_none_get_absolute_url(value):
    model = ModelWithGetAbsoluteUrl(value)
    result = resolve_url(model)
    assert result is None
    
    response = redirect(model)
    assert response["Location"] == "None"
```

**Failing input**: `None`

## Reproducing the Bug

```python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')

from django.conf import settings
settings.configure(
    DEBUG=True,
    SECRET_KEY='test',
    ROOT_URLCONF='test_urls',
)

import django
django.setup()

from django.shortcuts import resolve_url, redirect

class ModelWithNoneUrl:
    def get_absolute_url(self):
        return None

model = ModelWithNoneUrl()

result = resolve_url(model)
print(f"resolve_url returned: {result!r}")

response = redirect(model)
print(f"Location header: {response['Location']!r}")
```

## Why This Is A Bug

When `get_absolute_url()` returns `None`, this indicates the model doesn't have a valid URL. The current behavior creates an invalid redirect to the literal URL "None", which will cause 404 errors. The function should either raise an exception or handle None gracefully.

## Fix

```diff
--- a/django/shortcuts.py
+++ b/django/shortcuts.py
@@ -168,7 +168,11 @@ def resolve_url(to, *args, **kwargs):
     """
     # If it's a model, use get_absolute_url()
     if hasattr(to, "get_absolute_url"):
-        return to.get_absolute_url()
+        url = to.get_absolute_url()
+        if url is None:
+            raise ValueError(
+                f"{to.__class__.__name__}.get_absolute_url() returned None"
+            )
+        return url
 
     if isinstance(to, Promise):
         # Expand the lazy instance, as it can cause issues when it is passed
```