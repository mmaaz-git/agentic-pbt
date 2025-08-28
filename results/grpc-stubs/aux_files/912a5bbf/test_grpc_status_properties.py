#!/usr/bin/env python3
"""Property-based tests for grpc_status module using Hypothesis"""

import sys
import os

# Add the venv's site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import grpc
from grpc_status import rpc_status
from grpc_status._common import code_to_grpc_status_code, GRPC_DETAILS_METADATA_KEY
from google.rpc import status_pb2
from unittest.mock import Mock
import pytest


# Strategy for valid gRPC status codes
valid_status_codes = st.sampled_from([code.value[0] for code in grpc.StatusCode])

# Strategy for status messages
status_messages = st.text(min_size=0, max_size=1000)

# Strategy for invalid status codes
invalid_status_codes = st.integers().filter(
    lambda x: x not in [code.value[0] for code in grpc.StatusCode]
)


@given(valid_status_codes)
def test_code_to_grpc_status_code_valid(code):
    """Test that code_to_grpc_status_code handles all valid gRPC status codes."""
    result = code_to_grpc_status_code(code)
    assert isinstance(result, grpc.StatusCode)
    assert result.value[0] == code


@given(invalid_status_codes)
def test_code_to_grpc_status_code_invalid(code):
    """Test that code_to_grpc_status_code raises ValueError for invalid codes."""
    with pytest.raises(ValueError, match=f"Invalid status code {code}"):
        code_to_grpc_status_code(code)


@given(valid_status_codes, status_messages)
def test_to_status_properties(code, message):
    """Test properties of to_status function."""
    # Create a google.rpc.status.Status message
    status = status_pb2.Status()
    status.code = code
    status.message = message
    
    # Convert to grpc.Status
    grpc_status = rpc_status.to_status(status)
    
    # Check that the conversion preserves the code and message
    assert grpc_status.code.value[0] == code
    assert grpc_status.details == message
    
    # Check that trailing metadata contains the serialized status
    assert len(grpc_status.trailing_metadata) == 1
    key, value = grpc_status.trailing_metadata[0]
    assert key == GRPC_DETAILS_METADATA_KEY
    
    # Deserialize and verify round-trip
    deserialized_status = status_pb2.Status.FromString(value)
    assert deserialized_status.code == code
    assert deserialized_status.message == message


@given(valid_status_codes, status_messages)
def test_from_call_with_matching_status(code, message):
    """Test from_call when status code and message match."""
    # Create a mock call
    call = Mock()
    
    # Create a status proto
    status = status_pb2.Status()
    status.code = code
    status.message = message
    
    # Set up the mock call
    grpc_code = code_to_grpc_status_code(code)
    call.code.return_value = grpc_code
    call.details.return_value = message
    call.trailing_metadata.return_value = [
        (GRPC_DETAILS_METADATA_KEY, status.SerializeToString())
    ]
    
    # Call from_call
    result = rpc_status.from_call(call)
    
    # Verify the result
    assert result is not None
    assert result.code == code
    assert result.message == message


@given(valid_status_codes, status_messages, valid_status_codes, status_messages)
def test_from_call_with_mismatched_code(code1, message1, code2, message2):
    """Test that from_call raises ValueError when codes don't match."""
    assume(code1 != code2)  # Only test when codes are different
    
    # Create a mock call
    call = Mock()
    
    # Create a status proto with code1
    status = status_pb2.Status()
    status.code = code1
    status.message = message1
    
    # Set up the mock call with code2
    grpc_code = code_to_grpc_status_code(code2)
    call.code.return_value = grpc_code
    call.details.return_value = message1
    call.trailing_metadata.return_value = [
        (GRPC_DETAILS_METADATA_KEY, status.SerializeToString())
    ]
    
    # Should raise ValueError due to code mismatch
    with pytest.raises(ValueError, match="Code in Status proto .* doesn't match status code"):
        rpc_status.from_call(call)


@given(valid_status_codes, status_messages, status_messages)
def test_from_call_with_mismatched_message(code, message1, message2):
    """Test that from_call raises ValueError when messages don't match."""
    assume(message1 != message2)  # Only test when messages are different
    
    # Create a mock call
    call = Mock()
    
    # Create a status proto
    status = status_pb2.Status()
    status.code = code
    status.message = message1
    
    # Set up the mock call with different message
    grpc_code = code_to_grpc_status_code(code)
    call.code.return_value = grpc_code
    call.details.return_value = message2
    call.trailing_metadata.return_value = [
        (GRPC_DETAILS_METADATA_KEY, status.SerializeToString())
    ]
    
    # Should raise ValueError due to message mismatch
    with pytest.raises(ValueError, match="Message in Status proto .* doesn't match status details"):
        rpc_status.from_call(call)


@given(valid_status_codes, status_messages)
def test_from_call_returns_none_without_metadata(code, message):
    """Test that from_call returns None when there's no trailing metadata."""
    # Create a mock call with None trailing metadata
    call = Mock()
    call.trailing_metadata.return_value = None
    
    result = rpc_status.from_call(call)
    assert result is None


@given(valid_status_codes, status_messages)
def test_from_call_returns_none_without_grpc_details_key(code, message):
    """Test that from_call returns None when GRPC_DETAILS_METADATA_KEY is missing."""
    # Create a mock call with metadata but no GRPC_DETAILS_METADATA_KEY
    call = Mock()
    grpc_code = code_to_grpc_status_code(code)
    call.code.return_value = grpc_code
    call.details.return_value = message
    call.trailing_metadata.return_value = [
        ("some-other-key", b"some-value")
    ]
    
    result = rpc_status.from_call(call)
    assert result is None


@given(valid_status_codes, status_messages)
@settings(max_examples=100)
def test_round_trip_property(code, message):
    """Test round-trip property: to_status -> mock call -> from_call."""
    # Create a status
    status = status_pb2.Status()
    status.code = code
    status.message = message
    
    # Convert to grpc.Status
    grpc_status = rpc_status.to_status(status)
    
    # Create a mock call that represents the grpc_status
    call = Mock()
    call.code.return_value = grpc_status.code
    call.details.return_value = grpc_status.details
    call.trailing_metadata.return_value = grpc_status.trailing_metadata
    
    # Convert back using from_call
    result = rpc_status.from_call(call)
    
    # Verify round-trip
    assert result is not None
    assert result.code == status.code
    assert result.message == status.message


if __name__ == "__main__":
    # Run the tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])