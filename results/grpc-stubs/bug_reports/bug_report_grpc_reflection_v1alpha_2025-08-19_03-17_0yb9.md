# Bug Report: grpc_reflection.v1alpha ExtensionRequest Integer Overflow

**Target**: `grpc_reflection.v1alpha.reflection_pb2.ExtensionRequest`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

ExtensionRequest raises ValueError for extension_number values outside int32 range instead of handling them gracefully, causing crashes when processing valid protobuf data from other systems.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from grpc_reflection.v1alpha import reflection_pb2

@given(
    extension_number=st.integers()
)
def test_extension_request_integer_bounds(extension_number):
    """Test ExtensionRequest with various integer values."""
    request = reflection_pb2.ExtensionRequest(
        containing_type="test.Type",
        extension_number=extension_number
    )
    assert request.extension_number == extension_number
```

**Failing input**: `extension_number=2147483648`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages')

from grpc_reflection.v1alpha import reflection_pb2

request = reflection_pb2.ExtensionRequest(
    containing_type="test.Type",
    extension_number=2147483648  # Max int32 + 1
)
```

## Why This Is A Bug

The ExtensionRequest.extension_number field is defined as int32 in the protobuf schema, which limits it to the range [-2147483648, 2147483647]. However, when values outside this range are provided, the implementation raises a ValueError with "Value out of range" instead of:

1. Truncating to int32 bounds (common protobuf behavior)
2. Providing a more descriptive error message
3. Documenting this limitation in the type hints

This can cause unexpected crashes when processing data from external systems that might send int64 values or when using the API programmatically without knowing the exact bounds.

Additionally, the protobuf specification states that extension field numbers should be in the range [1, 536870911], but the implementation accepts any int32 value including 0 and negative numbers, which violates the protobuf specification.

## Fix

The issue is in the generated protobuf code which enforces strict int32 bounds. A potential fix would be to either:

1. Update the proto definition to use int64 if larger values are needed
2. Add input validation with better error messages
3. Document the int32 limitation in the stub files

For the stub file, add a note about the valid range:

```diff
--- a/grpc_reflection/v1alpha/reflection_pb2.pyi
+++ b/grpc_reflection/v1alpha/reflection_pb2.pyi
@@ -27,7 +27,7 @@ class ExtensionRequest(_message.Message):
     CONTAINING_TYPE_FIELD_NUMBER: _ClassVar[int]
     EXTENSION_NUMBER_FIELD_NUMBER: _ClassVar[int]
     containing_type: str
-    extension_number: int
+    extension_number: int  # Must be in range [-2147483648, 2147483647] (int32)
     def __init__(self, containing_type: _Optional[str] = ..., extension_number: _Optional[int] = ...) -> None: ...
```