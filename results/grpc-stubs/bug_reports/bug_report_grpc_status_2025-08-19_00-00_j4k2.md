# Bug Report: grpc_status Error Message Formatting with Special Characters

**Target**: `grpc_status.rpc_status.from_call`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `from_call` function in grpc_status produces poorly formatted error messages when status messages contain special characters like newlines, tabs, or carriage returns.

## Property-Based Test

```python
@given(valid_status_codes, status_messages, status_messages)
def test_from_call_with_mismatched_message(code, message1, message2):
    """Test that from_call raises ValueError when messages don't match."""
    assume(message1 != message2)
    
    call = Mock()
    
    status = status_pb2.Status()
    status.code = code
    status.message = message1
    
    grpc_code = code_to_grpc_status_code(code)
    call.code.return_value = grpc_code
    call.details.return_value = message2
    call.trailing_metadata.return_value = [
        (GRPC_DETAILS_METADATA_KEY, status.SerializeToString())
    ]
    
    with pytest.raises(ValueError, match="Message in Status proto .* doesn't match status details"):
        rpc_status.from_call(call)
```

**Failing input**: `code=0, message1='\n', message2=''`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages')

from unittest.mock import Mock
from grpc_status import rpc_status
from grpc_status._common import code_to_grpc_status_code, GRPC_DETAILS_METADATA_KEY
from google.rpc import status_pb2

call = Mock()

status = status_pb2.Status()
status.code = 0
status.message = '\n'

grpc_code = code_to_grpc_status_code(0)
call.code.return_value = grpc_code
call.details.return_value = ''
call.trailing_metadata.return_value = [
    (GRPC_DETAILS_METADATA_KEY, status.SerializeToString())
]

try:
    rpc_status.from_call(call)
except ValueError as e:
    print(e)
```

## Why This Is A Bug

The error message format string directly inserts the message values without proper escaping or representation, resulting in confusing output like "Message in Status proto (\n) doesn't match status details ()" where the newline is literally rendered, breaking the readability of the error message. This violates the expected behavior of clear, readable error messages that help developers debug issues.

## Fix

```diff
--- a/grpc_status/rpc_status.py
+++ b/grpc_status/rpc_status.py
@@ -56,9 +56,9 @@ def from_call(call):
                     % (code_to_grpc_status_code(rich_status.code), call.code())
                 )
             if call.details() != rich_status.message:
                 raise ValueError(
-                    "Message in Status proto (%s) doesn't match status details"
-                    " (%s)" % (rich_status.message, call.details())
+                    "Message in Status proto (%r) doesn't match status details"
+                    " (%r)" % (rich_status.message, call.details())
                 )
             return rich_status
     return None
```