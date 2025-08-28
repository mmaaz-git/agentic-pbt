# Bug Report: django.apps.AppConfig.create IndexError with Trailing Dot

**Target**: `django.apps.AppConfig.create`
**Severity**: Low
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

`AppConfig.create()` crashes with `IndexError: string index out of range` when given a module path ending with a dot (e.g., `'django.contrib.auth.'`).

## Property-Based Test

```python
def test_app_config_create_with_trailing_dot():
    """
    Property: Module paths with trailing dots should be handled appropriately
    """
    with pytest.raises(ImportError):  # Should raise ImportError, not IndexError
        AppConfig.create('django.contrib.auth.')
```

**Failing input**: `'django.contrib.auth.'`

## Reproducing the Bug

```python
import django
from django.conf import settings
from django.apps import AppConfig

settings.configure(
    DEBUG=True,
    SECRET_KEY='test',
    INSTALLED_APPS=[],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
)
django.setup()

config = AppConfig.create('django.contrib.auth.')
```

## Why This Is A Bug

When a module path ends with a dot, `entry.rpartition(".")` returns an empty string for the last component. The code then attempts to check `cls_name[0].isupper()` on this empty string, causing an IndexError. The function should handle this edge case gracefully and raise an appropriate ImportError instead.

## Fix

```diff
--- a/django/apps/config.py
+++ b/django/apps/config.py
@@ -169,7 +169,7 @@ class AppConfig:
             # then it was likely intended to be an app config class; if not,
             # an app module. Provide a nice error message in both cases.
             mod_path, _, cls_name = entry.rpartition(".")
-            if mod_path and cls_name[0].isupper():
+            if mod_path and cls_name and cls_name[0].isupper():
                 # We could simply re-trigger the string import exception, but
                 # we're going the extra mile and providing a better error
                 # message for typos in INSTALLED_APPS.
```