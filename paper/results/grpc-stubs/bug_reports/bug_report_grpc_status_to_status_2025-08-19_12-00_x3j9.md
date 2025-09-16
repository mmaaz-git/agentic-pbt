# Bug Report: grpc_status.rpc_status.to_status Undocumented ValueError Exception

**Target**: `grpc_status.rpc_status.to_status`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `to_status()` function raises an undocumented `ValueError` when given a Status message with an invalid gRPC status code (outside range 0-16), violating its API contract.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from google.rpc import status_pb2
from grpc_status import rpc_status
import pytest

@given(
    st.integers(min_value=17, max_value=1000),  # Invalid gRPC codes
    st.text(min_size=0, max_size=100)
)
def test_to_status_with_invalid_codes(code, message):
    """Test that to_status handles invalid status codes."""
    proto_status = status_pb2.Status()
    proto_status.code = code
    proto_status.message = message
    
    # The docstring doesn't mention this can raise ValueError
    with pytest.raises(ValueError, match=f"Invalid status code {code}"):
        rpc_status.to_status(proto_status)
```

**Failing input**: Any Status proto with `code >= 17` (e.g., code=17, message="test")

## Reproducing the Bug

```python
from google.rpc import status_pb2
from grpc_status import rpc_status

# Create a Status with invalid gRPC code
proto_status = status_pb2.Status()
proto_status.code = 17  # Outside valid gRPC range [0-16]
proto_status.message = "Test message"

# This raises ValueError but isn't documented
grpc_status = rpc_status.to_status(proto_status)
# ValueError: Invalid status code 17
```

## Why This Is A Bug

The function's docstring states it "Convert a google.rpc.status.Status message to grpc.Status" and returns "A grpc.Status instance" without mentioning any exceptions. Users expect either:
1. The function to always return a valid grpc.Status, or
2. The docstring to document potential exceptions

Since `google.rpc.status.Status.code` is a plain int32 field that can hold any value, but gRPC only defines status codes 0-16, this mismatch should be documented.

## Fix

Update the docstring to document the exception:

```diff
def to_status(status):
    """Convert a google.rpc.status.Status message to grpc.Status.

    This is an EXPERIMENTAL API.

    Args:
      status: a google.rpc.status.Status message representing the non-OK status
        to terminate the RPC with and communicate it to the client.

    Returns:
      A grpc.Status instance representing the input google.rpc.status.Status message.
+
+   Raises:
+     ValueError: If the status code is not a valid gRPC status code (0-16).
    """
```