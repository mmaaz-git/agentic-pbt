#!/usr/bin/env python3
"""Property-based tests for grpc_status module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from google.rpc import status_pb2
import grpc
from grpc_status import rpc_status
from grpc_status._common import code_to_grpc_status_code, GRPC_DETAILS_METADATA_KEY
from unittest.mock import Mock
import pytest


# Test 1: code_to_grpc_status_code mapping
@given(st.integers())
def test_code_to_grpc_status_code_bijection(code):
    """Test that code_to_grpc_status_code correctly maps valid codes and rejects invalid ones."""
    valid_codes = [status.value[0] for status in grpc.StatusCode]
    
    if code in valid_codes:
        # Valid codes should map correctly
        result = code_to_grpc_status_code(code)
        assert isinstance(result, grpc.StatusCode)
        assert result.value[0] == code
    else:
        # Invalid codes should raise ValueError
        with pytest.raises(ValueError, match=f"Invalid status code {code}"):
            code_to_grpc_status_code(code)


# Test 2: from_call validation properties
@given(
    st.integers(min_value=0, max_value=16),  # gRPC status codes range
    st.text(min_size=0, max_size=1000),  # message
    st.binary(min_size=0, max_size=1000)  # serialized proto
)
def test_from_call_validation(status_code, message, proto_bytes):
    """Test that from_call correctly validates consistency between call and Status proto."""
    
    # Create a mock call
    mock_call = Mock()
    mock_call.code.return_value = Mock(value=(status_code, ""))
    mock_call.details.return_value = message
    
    # Try to create a Status proto with potentially mismatched values
    try:
        rich_status = status_pb2.Status.FromString(proto_bytes)
        # If deserialization succeeds, set up the metadata
        mock_call.trailing_metadata.return_value = [
            (GRPC_DETAILS_METADATA_KEY, proto_bytes)
        ]
        
        # Test the validation
        try:
            result = rpc_status.from_call(mock_call)
            # If it succeeds, the codes and messages must match
            if result is not None:
                assert result.code == status_code
                assert result.message == message
        except ValueError as e:
            # ValueError should only occur on mismatch
            assert (rich_status.code != status_code) or (rich_status.message != message)
            
    except Exception:
        # If proto deserialization fails, test with empty metadata
        mock_call.trailing_metadata.return_value = []
        result = rpc_status.from_call(mock_call)
        assert result is None  # Should return None for no metadata


# Test 3: to_status creates valid Status objects
@given(
    st.integers(min_value=0, max_value=16),  # gRPC status codes
    st.text(min_size=0, max_size=1000)  # message
)
def test_to_status_creates_valid_status(code, message):
    """Test that to_status creates a valid grpc.Status from a google.rpc.Status."""
    
    # Create a google.rpc.status.Status
    proto_status = status_pb2.Status()
    proto_status.code = code
    proto_status.message = message
    
    # Convert to grpc.Status
    try:
        grpc_status = rpc_status.to_status(proto_status)
        
        # Verify the result
        assert isinstance(grpc_status.code, grpc.StatusCode)
        assert grpc_status.code.value[0] == code
        assert grpc_status.details == message
        assert len(grpc_status.trailing_metadata) == 1
        assert grpc_status.trailing_metadata[0][0] == GRPC_DETAILS_METADATA_KEY
        
        # The metadata should contain the serialized proto
        reconstructed = status_pb2.Status.FromString(grpc_status.trailing_metadata[0][1])
        assert reconstructed.code == code
        assert reconstructed.message == message
        
    except ValueError:
        # Should only fail for invalid codes
        valid_codes = [status.value[0] for status in grpc.StatusCode]
        assert code not in valid_codes


# Test 4: Round-trip property between to_status and parsing
@given(
    st.sampled_from([s.value[0] for s in grpc.StatusCode]),  # Only valid codes
    st.text(min_size=0, max_size=1000)
)
def test_to_status_round_trip(code, message):
    """Test round-trip: creating a Status and parsing it back yields the same data."""
    
    # Create original Status
    original_status = status_pb2.Status()
    original_status.code = code
    original_status.message = message
    
    # Convert to grpc.Status
    grpc_status = rpc_status.to_status(original_status)
    
    # Extract and parse the serialized proto from metadata
    serialized = grpc_status.trailing_metadata[0][1]
    recovered_status = status_pb2.Status.FromString(serialized)
    
    # Verify round-trip
    assert recovered_status.code == original_status.code
    assert recovered_status.message == original_status.message


# Test 5: from_call handles None trailing_metadata correctly
@given(st.integers(), st.text())
def test_from_call_none_metadata(code, details):
    """Test that from_call returns None when trailing_metadata is None."""
    mock_call = Mock()
    mock_call.code.return_value = Mock(value=(code, ""))
    mock_call.details.return_value = details
    mock_call.trailing_metadata.return_value = None
    
    result = rpc_status.from_call(mock_call)
    assert result is None


# Test 6: from_call handles missing grpc-status-details-bin key  
@given(
    st.lists(
        st.tuples(
            st.text(min_size=1).filter(lambda x: x != GRPC_DETAILS_METADATA_KEY),
            st.binary()
        ),
        min_size=0,
        max_size=10
    )
)
def test_from_call_missing_key(metadata_list):
    """Test that from_call returns None when the special key is missing."""
    mock_call = Mock()
    mock_call.trailing_metadata.return_value = metadata_list
    
    result = rpc_status.from_call(mock_call)
    assert result is None