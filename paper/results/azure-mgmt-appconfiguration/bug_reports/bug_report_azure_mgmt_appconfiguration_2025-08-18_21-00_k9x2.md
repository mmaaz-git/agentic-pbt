# Bug Report: azure-mgmt-appconfiguration Readonly Fields Can Be Modified After Creation

**Target**: `azure.mgmt.appconfiguration.models`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Fields marked as readonly in model validation dictionaries can be modified after object creation, violating the expected immutability contract for readonly fields.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from azure.mgmt.appconfiguration.models import ApiKey, ConfigurationStore

@given(
    new_id=st.text(min_size=1),
    new_name=st.text(min_size=1),
    new_value=st.text(min_size=1),
)
def test_readonly_fields_should_be_immutable(new_id, new_name, new_value):
    """Test that readonly fields cannot be modified after creation"""
    # Create an ApiKey with readonly fields
    api_key = ApiKey()
    
    # These fields are marked readonly in _validation
    original_id = api_key.id
    original_name = api_key.name
    
    # Attempt to modify readonly fields
    api_key.id = new_id
    api_key.name = new_name
    api_key.value = new_value
    
    # Bug: The modifications succeed when they should be prevented
    assert api_key.id == new_id  # This passes but shouldn't
    assert api_key.name == new_name  # This passes but shouldn't
    assert api_key.value == new_value  # This passes but shouldn't
```

**Failing input**: Any non-None string values for `new_id`, `new_name`, `new_value`

## Reproducing the Bug

```python
from azure.mgmt.appconfiguration.models import ApiKey

# Create an ApiKey instance
api_key = ApiKey()

# The id field is marked as readonly in the model
print(f"Initial id: {api_key.id}")  # None

# Modify the readonly field - this should not be allowed
api_key.id = "modified-id"

# Bug: The modification succeeds
print(f"Modified id: {api_key.id}")  # "modified-id"
assert api_key.id == "modified-id"  # This assertion passes!
```

## Why This Is A Bug

The ApiKey model (and other models like ConfigurationStore) define certain fields as readonly in their `_validation` dictionary:

```python
_validation = {
    "id": {"readonly": True},
    "name": {"readonly": True},
    "value": {"readonly": True},
    # ... other readonly fields
}
```

These readonly fields represent server-generated values that should not be modifiable by client code. However, the current implementation only validates readonly status during `__init__` (logging a warning if readonly fields are passed as kwargs) but does not prevent modification after object creation. This violates the principle of immutability for readonly fields and could lead to:

1. **Data inconsistency**: Client code might accidentally modify server-generated IDs or timestamps
2. **API contract violations**: Modified readonly fields could be sent to the server in API calls
3. **Debugging difficulties**: Readonly fields changing unexpectedly makes debugging harder

## Fix

The fix would involve implementing property descriptors or using `__setattr__` to enforce readonly constraints:

```diff
class Model:
    """Mixin for all client request body/response body models"""
    
+   def __setattr__(self, key, value):
+       # Check if this is a readonly field after initialization
+       if hasattr(self, '_initialized') and self._initialized:
+           validation = getattr(self.__class__, '_validation', {})
+           if key in validation and validation[key].get('readonly', False):
+               raise AttributeError(f"Cannot modify readonly field '{key}'")
+       super().__setattr__(key, value)
    
    def __init__(self, **kwargs):
        self.additional_properties = {}
        for k in kwargs:
            if k not in self._attribute_map:
                _LOGGER.warning("%s is not a known attribute of class %s and will be ignored", k, self.__class__)
            elif k in self._validation and self._validation[k].get("readonly", False):
                _LOGGER.warning("Readonly attribute %s will be ignored in class %s", k, self.__class__)
            else:
                setattr(self, k, kwargs[k])
+       self._initialized = True
```

This would ensure that readonly fields cannot be modified after the object is created, maintaining the intended immutability contract.