# Bug Report: grpc_status._async Error Message Formatting with Special Characters

**Target**: `grpc_status._async.from_call`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The async `from_call` function in grpc_status._async produces poorly formatted error messages when status messages contain special characters, identical to the bug in the synchronous version.

## Property-Based Test

```python
@given(valid_status_codes, status_messages, status_messages)
async def test_async_from_call_with_mismatched_message(code, message1, message2):
    """Test that async from_call raises ValueError when messages don't match."""
    assume(message1 != message2)
    
    call = Mock()
    
    status = status_pb2.Status()
    status.code = code
    status.message = message1
    
    grpc_code = code_to_grpc_status_code(code)
    call.code = AsyncMock(return_value=grpc_code)
    call.details = AsyncMock(return_value=message2)
    call.trailing_metadata = AsyncMock(return_value=[
        (GRPC_DETAILS_METADATA_KEY, status.SerializeToString())
    ])
    
    with pytest.raises(ValueError):
        await from_call(call)
```

**Failing input**: `code=0, message1='\n', message2=''`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages')

import asyncio
from unittest.mock import Mock, AsyncMock
from grpc_status._async import from_call
from grpc_status._common import code_to_grpc_status_code, GRPC_DETAILS_METADATA_KEY
from google.rpc import status_pb2

async def reproduce():
    call = Mock()
    
    status = status_pb2.Status()
    status.code = 0
    status.message = '\n'
    
    grpc_code = code_to_grpc_status_code(0)
    
    call.code = AsyncMock(return_value=grpc_code)
    call.details = AsyncMock(return_value='')
    call.trailing_metadata = AsyncMock(return_value=[
        (GRPC_DETAILS_METADATA_KEY, status.SerializeToString())
    ])
    
    try:
        await from_call(call)
    except ValueError as e:
        print(e)

asyncio.run(reproduce())
```

## Why This Is A Bug

The async version suffers from the same issue as the synchronous version: error messages directly insert message values without proper escaping, resulting in confusing output with literal special characters that break readability.

## Fix

```diff
--- a/grpc_status/_async.py
+++ b/grpc_status/_async.py
@@ -45,9 +45,9 @@ async def from_call(call: aio.Call):
                     % (code_to_grpc_status_code(rich_status.code), code)
                 )
             if details != rich_status.message:
                 raise ValueError(
-                    "Message in Status proto (%s) doesn't match status details"
-                    " (%s)" % (rich_status.message, details)
+                    "Message in Status proto (%r) doesn't match status details"
+                    " (%r)" % (rich_status.message, details)
                 )
             return rich_status
     return None
```