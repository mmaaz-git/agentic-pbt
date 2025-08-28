#!/usr/bin/env python3
"""Test error message formatting with various special characters"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages')

from unittest.mock import Mock
from grpc_status import rpc_status
from grpc_status._common import code_to_grpc_status_code, GRPC_DETAILS_METADATA_KEY
from google.rpc import status_pb2

def test_special_char(char_desc, message_value):
    call = Mock()
    
    status = status_pb2.Status()
    status.code = 0
    status.message = message_value
    
    grpc_code = code_to_grpc_status_code(0)
    call.code.return_value = grpc_code
    call.details.return_value = 'different'
    call.trailing_metadata.return_value = [
        (GRPC_DETAILS_METADATA_KEY, status.SerializeToString())
    ]
    
    try:
        rpc_status.from_call(call)
    except ValueError as e:
        print(f"{char_desc}: {repr(str(e))}")

# Test various special characters
test_special_char("Newline", "\n")
test_special_char("Tab", "\t")
test_special_char("Carriage return", "\r")
test_special_char("Multiple newlines", "\n\n\n")
test_special_char("Mixed whitespace", "\n\t\r ")
test_special_char("Very long message", "A" * 1000)