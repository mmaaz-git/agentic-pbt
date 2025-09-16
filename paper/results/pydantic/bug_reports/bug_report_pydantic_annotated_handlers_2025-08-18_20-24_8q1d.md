# Bug Report: pydantic.annotated_handlers GetJsonSchemaHandler.mode Attribute Not Initialized

**Target**: `pydantic.annotated_handlers.GetJsonSchemaHandler`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

GetJsonSchemaHandler's docstring documents a `mode` attribute, but accessing it raises AttributeError because the attribute is never initialized.

## Property-Based Test

```python
def test_json_handler_mode_attribute_contract():
    """
    The GetJsonSchemaHandler docstring states:
    'Attributes:
        mode: Json schema mode, can be `validation` or `serialization`.'
    
    This implies the attribute should be accessible, but it raises AttributeError.
    """
    handler = GetJsonSchemaHandler()
    with pytest.raises(AttributeError):
        _ = handler.mode
```

**Failing input**: No specific input - fails on attribute access

## Reproducing the Bug

```python
from pydantic.annotated_handlers import GetJsonSchemaHandler

handler = GetJsonSchemaHandler()
print(handler.mode)  # Raises: AttributeError: 'GetJsonSchemaHandler' object has no attribute 'mode'
```

## Why This Is A Bug

The class docstring explicitly documents `mode` as an attribute that "can be `validation` or `serialization`", implying it should be accessible. However, the attribute is only type-annotated but never initialized, causing AttributeError on access. This violates the documented API contract.

## Fix

```diff
class GetJsonSchemaHandler:
    """Handler to call into the next JSON schema generation function.

    Attributes:
        mode: Json schema mode, can be `validation` or `serialization`.
    """

    mode: JsonSchemaMode
+   
+   def __init__(self, mode: JsonSchemaMode = 'validation'):
+       self.mode = mode

    def __call__(self, core_schema: CoreSchemaOrField, /) -> JsonSchemaValue:
```