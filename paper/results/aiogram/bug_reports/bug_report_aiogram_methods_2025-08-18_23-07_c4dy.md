# Bug Report: aiogram.methods JSON Serialization Fails with Default Values

**Target**: `aiogram.methods`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `model_dump_json()` method fails with a `PydanticSerializationError` when called on any aiogram method class that contains Default objects in its fields.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from aiogram.methods import SendMessage
from aiogram.client.default import Default
import pytest

@given(
    chat_id=st.integers(min_value=-999999999999, max_value=999999999999),
    text=st.text(min_size=1, max_size=4096)
)
def test_sendmessage_serialization_with_defaults(chat_id, text):
    msg = SendMessage(chat_id=chat_id, text=text)
    dumped = msg.model_dump()
    
    has_defaults = any(isinstance(v, Default) for v in dumped.values())
    if has_defaults:
        with pytest.raises(Exception) as exc_info:
            msg.model_dump_json()
        assert "serialize" in str(exc_info.value).lower() or "Default" in str(exc_info.value)
```

**Failing input**: Any valid input triggers the bug (e.g., `chat_id=123456789, text="Hello World"`)

## Reproducing the Bug

```python
from aiogram.methods import SendMessage

msg = SendMessage(chat_id=123456789, text="Hello World")

dumped = msg.model_dump()
print(f"model_dump() works: {type(dumped)}")

try:
    json_str = msg.model_dump_json()
    print(f"model_dump_json() result: {json_str}")
except Exception as e:
    print(f"model_dump_json() failed: {e}")
```

## Why This Is A Bug

The `model_dump_json()` method is a standard Pydantic operation that should work for all Pydantic models. The presence of Default objects (which are aiogram-specific sentinel values) prevents JSON serialization, making it impossible to serialize these models to JSON without using workarounds like `exclude_unset=True`. This breaks the expected Pydantic contract and makes the models harder to work with in contexts that require JSON serialization.

## Fix

The Default class needs a custom Pydantic serializer. Here's a potential fix:

```diff
# In aiogram/client/default.py
+from pydantic import field_serializer
+from typing import Any

 class Default:
     def __init__(self, name: str) -> None:
         self.name = name
 
     def __repr__(self) -> str:
         return f"Default({self.name!r})"
+
+    @classmethod
+    def __get_pydantic_core_schema__(cls, source, handler):
+        from pydantic_core import core_schema
+        
+        def serialize_default(instance: 'Default', info) -> Any:
+            # Option 1: Serialize as None
+            return None
+            # Option 2: Serialize as a string marker
+            # return f"__default__{instance.name}__"
+            # Option 3: Exclude from serialization
+            # raise ValueError("Default values should be excluded")
+        
+        return core_schema.with_info_plain_validator_function(
+            lambda v, info: v,
+            serialization=core_schema.plain_serializer_function_ser_schema(
+                serialize_default,
+                return_schema=core_schema.any_schema(),
+            )
+        )
```

Alternatively, the method classes could override `model_dump_json()` to automatically exclude Default values or replace them with None during serialization.