# Bug Report: simple_history.management.commands.clean_duplicate_history Missing Attribute Initialization

**Target**: `simple_history.management.commands.clean_duplicate_history.Command`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `Command` class in `clean_duplicate_history.py` has methods that assume certain instance attributes exist (`excluded_fields` and `base_manager`), but these attributes are only initialized in the `handle()` method, causing AttributeError when methods are called directly.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from simple_history.management.commands.clean_duplicate_history import Command
from unittest.mock import Mock

@given(dry_run=st.booleans())
def test_check_and_delete_missing_excluded_fields(dry_run):
    cmd = Command()
    entry1 = Mock()
    entry2 = Mock()
    mock_delta = Mock()
    mock_delta.changed_fields = []
    entry1.diff_against.return_value = mock_delta
    
    # This fails with AttributeError: 'Command' object has no attribute 'excluded_fields'
    result = cmd._check_and_delete(entry1, entry2, dry_run=dry_run)
```

**Failing input**: `dry_run=False` (any boolean value causes the error)

## Reproducing the Bug

```python
import sys
import os
from unittest.mock import Mock

sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_settings'

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'simple_history'],
        USE_TZ=True,
        SECRET_KEY='test-secret-key',
    )
    django.setup()

from simple_history.management.commands.clean_duplicate_history import Command

cmd = Command()

# Test 1: Missing excluded_fields
entry1 = Mock()
entry2 = Mock()
mock_delta = Mock()
mock_delta.changed_fields = []
entry1.diff_against.return_value = mock_delta

try:
    cmd._check_and_delete(entry1, entry2, dry_run=True)
except AttributeError as e:
    print(f"Error 1: {e}")

# Test 2: Missing base_manager  
cmd.verbosity = 0
mock_model = Mock()
mock_model._meta.pk.name = 'id'
mock_model._base_manager.all.return_value.iterator.return_value = iter([])
mock_model._default_manager.all.return_value.iterator.return_value = iter([])
mock_history_model = Mock()
mock_history_model.objects.filter.return_value.count.return_value = 0
mock_history_model.objects.filter.return_value.exists.return_value = False

try:
    cmd._process([(mock_model, mock_history_model)], date_back=None, dry_run=True)
except AttributeError as e:
    print(f"Error 2: {e}")
```

## Why This Is A Bug

The `_check_and_delete` and `_process` methods are designed to be callable as part of the command's internal API, but they assume that `self.excluded_fields` and `self.base_manager` exist. These attributes are only set in `handle()`, making the methods unusable when called directly (e.g., in unit tests or when subclassing). This violates the principle that methods should either be self-contained or properly initialize their dependencies.

## Fix

```diff
--- a/simple_history/management/commands/clean_duplicate_history.py
+++ b/simple_history/management/commands/clean_duplicate_history.py
@@ -15,6 +15,14 @@ class Command(populate_history.Command):
     
     DONE_CLEANING_FOR_MODEL = "Removed {count} historical records for {model}\n"
 
+    def __init__(self, *args, **kwargs):
+        super().__init__(*args, **kwargs)
+        # Initialize attributes that are used in methods but only set in handle()
+        # This ensures methods can be called independently without AttributeError
+        self.excluded_fields = None
+        self.base_manager = False
+        self.verbosity = 1
+
     def add_arguments(self, parser):
         parser.add_argument("models", nargs="*", type=str)
         parser.add_argument(
```