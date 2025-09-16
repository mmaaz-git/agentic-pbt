#!/usr/bin/env python3
"""Minimal reproduction of the bug in grpc_status.rpc_status.from_call"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages')

from unittest.mock import Mock
from grpc_status import rpc_status
from grpc_status._common import code_to_grpc_status_code, GRPC_DETAILS_METADATA_KEY
from google.rpc import status_pb2

# Create a mock call
call = Mock()

# Create a status proto with a newline in the message
status = status_pb2.Status()
status.code = 0
status.message = '\n'

# Set up the mock call with empty string message
grpc_code = code_to_grpc_status_code(0)
call.code.return_value = grpc_code
call.details.return_value = ''  # Different from status.message
call.trailing_metadata.return_value = [
    (GRPC_DETAILS_METADATA_KEY, status.SerializeToString())
]

try:
    rpc_status.from_call(call)
except ValueError as e:
    print(f"ValueError raised: {e}")
    print(f"Error message contains newline: {repr(str(e))}")