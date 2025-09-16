# Bug Report: simple_history.models transform_field AttributeError

**Target**: `simple_history.models.transform_field`
**Severity**: Low
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `transform_field` function crashes with AttributeError when called on Django field objects that are not attached to a model, as these fields lack the `attname` attribute.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from django.db import models
from simple_history.models import transform_field

@given(
    st.builds(
        models.CharField,
        max_length=st.integers(min_value=1, max_value=255)
    )
)
def test_transform_field_on_unattached_fields(field):
    """Test that transform_field works on fields not attached to models"""
    transform_field(field)  # Should not raise AttributeError
```

**Failing input**: Any Django field created directly without being attached to a model

## Reproducing the Bug

```python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')

from django.conf import settings
if not settings.configured:
    settings.configure(
        SECRET_KEY='test',
        INSTALLED_APPS=['django.contrib.contenttypes'],
    )

import django
django.setup()

from django.db import models
from simple_history.models import transform_field

# Create a field not attached to a model
field = models.CharField(max_length=100)

# This raises AttributeError
transform_field(field)
```

## Why This Is A Bug

The `transform_field` function is a module-level public function that should handle any valid Django field object. However, it assumes all fields have an `attname` attribute, which is only present on fields attached to models. This violates the principle that public functions should handle their documented input domain gracefully.

## Fix

```diff
--- a/simple_history/models.py
+++ b/simple_history/models.py
@@ -818,7 +818,10 @@ def transform_field(field):
 
 def transform_field(field):
     """Customize field appropriately for use in historical model"""
-    field.name = field.attname
+    if hasattr(field, 'attname'):
+        field.name = field.attname
+    elif not field.name:
+        field.name = None
     if isinstance(field, models.BigAutoField):
         field.__class__ = models.BigIntegerField
     elif isinstance(field, models.AutoField):
```