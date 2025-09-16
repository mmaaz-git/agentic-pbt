# Bug Report: simple_history.utils TypeError with None Primary Key Name

**Target**: `simple_history.utils.get_app_model_primary_key_name`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `get_app_model_primary_key_name` function crashes with a TypeError when a model has a ForeignKey primary key with `None` as its name, attempting to concatenate `None + "_id"`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from unittest.mock import Mock
from django.db.models import ForeignKey
import simple_history.utils as utils

def test_foreignkey_with_none_name():
    mock_model = Mock()
    mock_pk = Mock(spec=ForeignKey)
    mock_pk.name = None
    mock_model._meta = Mock()
    mock_model._meta.pk = mock_pk
    
    try:
        result = utils.get_app_model_primary_key_name(mock_model)
        assert False, "Expected TypeError"
    except TypeError as e:
        assert "unsupported operand" in str(e) or "NoneType" in str(e)
```

**Failing input**: Model with ForeignKey primary key where `pk.name = None`

## Reproducing the Bug

```python
import simple_history.utils as utils
from unittest.mock import Mock
from django.db.models import ForeignKey

mock_model = Mock()
mock_pk = Mock(spec=ForeignKey)
mock_pk.name = None
mock_model._meta = Mock()
mock_model._meta.pk = mock_pk

result = utils.get_app_model_primary_key_name(mock_model)
```

## Why This Is A Bug

The function assumes `pk.name` is always a string but doesn't handle the case where it could be `None`. This causes a TypeError when attempting string concatenation (`None + "_id"`), which propagates to other functions that call `get_app_model_primary_key_name`, including `get_history_manager_from_history`.

## Fix

```diff
def get_app_model_primary_key_name(model):
    """Return the primary key name for a given app model."""
+   if model._meta.pk.name is None:
+       return None
    if isinstance(model._meta.pk, ForeignKey):
        return model._meta.pk.name + "_id"
    return model._meta.pk.name
```