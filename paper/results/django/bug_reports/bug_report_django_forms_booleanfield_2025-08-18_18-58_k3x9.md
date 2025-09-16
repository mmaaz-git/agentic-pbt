# Bug Report: django.forms.BooleanField Counterintuitive String Interpretation  

**Target**: `django.forms.BooleanField`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

BooleanField.clean() interprets the strings 'no' and 'off' as True, which is counterintuitive and inconsistent with user expectations for these common negative terms.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from django.forms import BooleanField

@given(st.sampled_from(['no', 'off', 'yes', 'on', 'true', 'false']))
def test_booleanfield_intuitive_string_parsing(value_str):
    field = BooleanField(required=False)
    result = field.clean(value_str)
    
    # Intuitive expectations
    if value_str in ['no', 'off', 'false']:
        assert result is False, f"'{value_str}' should be False"
    elif value_str in ['yes', 'on', 'true']:
        assert result is True, f"'{value_str}' should be True"
```

**Failing input**: `'no'` and `'off'`

## Reproducing the Bug

```python
import django
from django.conf import settings

settings.configure(DEBUG=True, SECRET_KEY='test')
django.setup()

from django.forms import BooleanField

field = BooleanField(required=False)

# Bug: 'no' and 'off' are interpreted as True
print(f"field.clean('no') = {field.clean('no')}")    # True (should be False)
print(f"field.clean('off') = {field.clean('off')}")  # True (should be False)

# These work as expected
print(f"field.clean('yes') = {field.clean('yes')}")      # True (correct)
print(f"field.clean('false') = {field.clean('false')}")  # False (correct)
print(f"field.clean('0') = {field.clean('0')}")          # False (correct)
```

## Why This Is A Bug

The strings 'no' and 'off' are universally understood as negative/false values in user interfaces. Having them evaluate to True violates the principle of least surprise and could lead to data entry errors where users selecting "no" have their choice recorded as "yes". This is particularly problematic in forms where these strings might come from select dropdowns or radio buttons.

## Fix

BooleanField's CheckboxInput widget treats any non-empty value as True except for specific false strings. The list of false strings should be expanded to include common negative terms:

```diff
# In django/forms/widgets.py CheckboxInput.value_from_datadict() or BooleanField.to_python()
- false_values = ['false', 'False', '0']
+ false_values = ['false', 'False', '0', 'no', 'No', 'off', 'Off']
```