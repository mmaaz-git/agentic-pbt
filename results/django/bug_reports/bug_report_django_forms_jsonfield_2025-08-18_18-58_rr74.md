# Bug Report: django.forms.JSONField Empty Collection Becomes None

**Target**: `django.forms.JSONField`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

JSONField.clean() incorrectly converts empty Python collections ([] and {}) to None when they are passed directly as Python objects, breaking round-trip properties.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from django.forms import JSONField

json_strategy = st.recursive(
    st.one_of(
        st.booleans(),
        st.integers(min_value=-1e10, max_value=1e10),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(min_size=0, max_size=100)
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(st.text(min_size=1, max_size=20), children, max_size=10)
    ),
    max_leaves=50
)

@given(json_strategy)
def test_jsonfield_preserves_python_objects(data):
    field = JSONField(required=False)
    cleaned = field.clean(data)
    assert cleaned == data
```

**Failing input**: `[]` and `{}`

## Reproducing the Bug

```python
import django
from django.conf import settings

settings.configure(DEBUG=True, SECRET_KEY='test')
django.setup()

from django.forms import JSONField

field = JSONField(required=False)

# Bug: Empty collections become None
empty_list = []
result = field.clean(empty_list)
print(f"field.clean([]) = {result}")  # None instead of []

empty_dict = {}
result = field.clean(empty_dict)
print(f"field.clean({{}}) = {result}")  # None instead of {}

# Non-empty collections work correctly
print(f"field.clean([1]) = {field.clean([1])}")  # [1] - correct
print(f"field.clean({{'a': 1}}) = {field.clean({'a': 1})}")  # {'a': 1} - correct
```

## Why This Is A Bug

JSONField should preserve the distinction between empty collections and None. Empty lists/dicts are valid JSON values distinct from null. This breaks the expected round-trip property where a value passed to clean() should be preserved if valid. The inconsistency between empty and non-empty collections suggests this is unintentional behavior.

## Fix

The issue likely lies in how JSONField checks for empty values. The field appears to be treating empty collections as "empty" in the validation sense, similar to empty strings.

```diff
# In django/forms/fields.py JSONField.to_python() or similar method
- if value in self.empty_values:  # [] and {} evaluate as False
+ if value in self.empty_values and not isinstance(value, (list, dict)):
      return None
```