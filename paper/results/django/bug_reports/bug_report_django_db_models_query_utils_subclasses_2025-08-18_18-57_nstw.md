# Bug Report: django.db.models.query_utils.subclasses TypeError with object class

**Target**: `django.db.models.query_utils.subclasses`
**Severity**: Low
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `subclasses` function raises a TypeError when called with the `object` class, failing to handle this special case of Python's type hierarchy.

## Property-Based Test

```python
from django.db.models.query_utils import subclasses
from hypothesis import given, strategies as st

@given(st.sampled_from([int, str, list, dict, Exception, BaseException, object]))
def test_subclasses_includes_self(cls):
    """Property: subclasses(cls) should always yield cls as first item"""
    result = list(subclasses(cls))
    assert len(result) >= 1, "Should yield at least the class itself"
    assert result[0] is cls, "First yielded item should be the input class"
```

**Failing input**: `object`

## Reproducing the Bug

```python
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
)
django.setup()

from django.db.models.query_utils import subclasses

result = list(subclasses(object))
```

## Why This Is A Bug

The `subclasses` function is expected to work with any class object to recursively yield all subclasses. However, it fails with Python's base `object` class due to calling `cls.__subclasses__()` which requires special handling for the `object` type. This violates the expected behavior that any class can be passed to the function.

## Fix

The issue occurs because `object.__subclasses__()` behaves differently from other classes. Here's a fix:

```diff
def subclasses(cls):
    yield cls
-   for subclass in cls.__subclasses__():
+   # Handle special case for object class
+   if cls is object:
+       subclasses_list = type.__subclasses__(object)
+   else:
+       subclasses_list = cls.__subclasses__()
+   for subclass in subclasses_list:
        yield from subclasses(subclass)
```