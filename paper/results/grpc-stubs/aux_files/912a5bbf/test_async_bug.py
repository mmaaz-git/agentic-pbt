#!/usr/bin/env python3
"""Check if the async version has the same bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages')

import asyncio
from unittest.mock import Mock, AsyncMock
from grpc_status._async import from_call
from grpc_status._common import code_to_grpc_status_code, GRPC_DETAILS_METADATA_KEY
from google.rpc import status_pb2

async def test_async_error_message():
    call = Mock()
    
    status = status_pb2.Status()
    status.code = 0
    status.message = '\n'
    
    grpc_code = code_to_grpc_status_code(0)
    
    # Set up async mocks
    call.code = AsyncMock(return_value=grpc_code)
    call.details = AsyncMock(return_value='')
    call.trailing_metadata = AsyncMock(return_value=[
        (GRPC_DETAILS_METADATA_KEY, status.SerializeToString())
    ])
    
    try:
        await from_call(call)
    except ValueError as e:
        print(f"Async version error: {repr(str(e))}")
        return str(e)

# Run the async test
result = asyncio.run(test_async_error_message())
print(f"\nSame bug in async version: {'(\n)' in result}")