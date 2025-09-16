#!/usr/bin/env python3
"""Edge case property-based tests for grpc_reflection module."""

import sys
import os

# Add the environment's site-packages to Python path
sys.path.insert(0, '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, seed, note
from hypothesis.strategies import composite
import pytest
from unittest.mock import Mock, MagicMock, patch
from google.protobuf import descriptor_pb2

# Import the modules to test
from grpc_reflection.v1alpha import reflection_pb2
from grpc_reflection.v1alpha import reflection_pb2_grpc
from grpc_reflection.v1alpha._base import BaseReflectionServicer, _collect_transitive_dependencies, _not_found_error
from grpc_reflection.v1alpha.reflection import ReflectionServicer
from grpc_reflection.v1alpha.proto_reflection_descriptor_database import ProtoReflectionDescriptorDatabase
import grpc


# Test edge cases with empty or extreme values
@given(
    file_descriptor_protos=st.lists(st.binary(min_size=0, max_size=1000), min_size=0, max_size=100)
)
def test_file_descriptor_response_with_empty_or_binary_data(file_descriptor_protos):
    """Test FileDescriptorResponse with various binary data."""
    response = reflection_pb2.FileDescriptorResponse(
        file_descriptor_proto=file_descriptor_protos
    )
    
    # Should be able to serialize and deserialize
    serialized = response.SerializeToString()
    deserialized = reflection_pb2.FileDescriptorResponse()
    deserialized.ParseFromString(serialized)
    
    # Data should be preserved
    assert list(deserialized.file_descriptor_proto) == file_descriptor_protos


@given(
    extension_numbers=st.lists(st.integers(min_value=-2147483648, max_value=2147483647), min_size=0, max_size=100)
)
def test_extension_number_response_with_negative_numbers(extension_numbers):
    """Test ExtensionNumberResponse with negative or extreme extension numbers."""
    response = reflection_pb2.ExtensionNumberResponse(
        base_type_name="test.Type",
        extension_number=extension_numbers
    )
    
    serialized = response.SerializeToString()
    deserialized = reflection_pb2.ExtensionNumberResponse()
    deserialized.ParseFromString(serialized)
    
    assert list(deserialized.extension_number) == extension_numbers


@given(
    service_names=st.lists(
        st.text(min_size=0, max_size=1000),
        min_size=0,
        max_size=100
    )
)
def test_service_response_with_empty_names(service_names):
    """Test ServiceResponse with empty or very long service names."""
    services = [reflection_pb2.ServiceResponse(name=name) for name in service_names]
    response = reflection_pb2.ListServiceResponse(service=services)
    
    serialized = response.SerializeToString()
    deserialized = reflection_pb2.ListServiceResponse()
    deserialized.ParseFromString(serialized)
    
    deserialized_names = [s.name for s in deserialized.service]
    assert deserialized_names == service_names


# Test concurrent request handling
@given(
    request_types=st.lists(
        st.sampled_from(['file_by_filename', 'file_containing_symbol', 'list_services', 'empty']),
        min_size=1,
        max_size=10
    )
)
def test_reflection_servicer_multiple_requests(request_types):
    """Test ReflectionServicer handling multiple requests in sequence."""
    servicer = ReflectionServicer(['service1', 'service2'])
    requests = []
    
    for req_type in request_types:
        if req_type == 'file_by_filename':
            req = reflection_pb2.ServerReflectionRequest(file_by_filename="test.proto")
        elif req_type == 'file_containing_symbol':
            req = reflection_pb2.ServerReflectionRequest(file_containing_symbol="TestMessage")
        elif req_type == 'list_services':
            req = reflection_pb2.ServerReflectionRequest(list_services="")
        else:  # empty
            req = reflection_pb2.ServerReflectionRequest()
        requests.append(req)
    
    context = Mock()
    responses = list(servicer.ServerReflectionInfo(iter(requests), context))
    
    # Should get same number of responses as requests
    assert len(responses) == len(requests)
    
    # Each response should have original_request field
    for i, response in enumerate(responses):
        assert response.original_request == requests[i]


# Test error message encoding
@given(
    error_message=st.text(min_size=0, max_size=10000)
)
def test_error_response_with_unicode_messages(error_message):
    """Test ErrorResponse with various unicode characters in error messages."""
    error_code = 13  # INTERNAL
    response = reflection_pb2.ErrorResponse(
        error_code=error_code,
        error_message=error_message
    )
    
    serialized = response.SerializeToString()
    deserialized = reflection_pb2.ErrorResponse()
    deserialized.ParseFromString(serialized)
    
    assert deserialized.error_code == error_code
    assert deserialized.error_message == error_message


# Test dependency collection with complex graphs
def test_collect_dependencies_with_shared_dependencies():
    """Test _collect_transitive_dependencies with diamond dependency pattern."""
    # Create diamond pattern: D depends on B and C, both depend on A
    file_a = Mock()
    file_a.name = "a.proto"
    file_a.dependencies = []
    
    file_b = Mock()
    file_b.name = "b.proto"
    file_b.dependencies = [file_a]
    
    file_c = Mock()
    file_c.name = "c.proto"
    file_c.dependencies = [file_a]
    
    file_d = Mock()
    file_d.name = "d.proto"
    file_d.dependencies = [file_b, file_c]
    
    seen_files = {}
    _collect_transitive_dependencies(file_d, seen_files)
    
    # All files should be collected exactly once
    assert len(seen_files) == 4
    assert "a.proto" in seen_files
    assert "b.proto" in seen_files
    assert "c.proto" in seen_files
    assert "d.proto" in seen_files


# Test with malformed requests
@given(
    containing_type=st.text(min_size=0, max_size=1000),
    extension_number=st.integers()
)
def test_extension_request_with_extreme_values(containing_type, extension_number):
    """Test ExtensionRequest with extreme or unusual values."""
    request = reflection_pb2.ExtensionRequest(
        containing_type=containing_type,
        extension_number=extension_number
    )
    
    # Create a ServerReflectionRequest with this extension request
    server_request = reflection_pb2.ServerReflectionRequest(
        file_containing_extension=request
    )
    
    # Should be able to serialize/deserialize
    serialized = server_request.SerializeToString()
    deserialized = reflection_pb2.ServerReflectionRequest()
    deserialized.ParseFromString(serialized)
    
    assert deserialized.file_containing_extension.containing_type == containing_type
    assert deserialized.file_containing_extension.extension_number == extension_number


# Test ProtoReflectionDescriptorDatabase error handling
@given(
    key_type=st.sampled_from(['string', 'tuple']),
    key_value=st.text(min_size=1, max_size=100)
)
def test_proto_reflection_db_keyerror_handling(key_type, key_value):
    """Test that ProtoReflectionDescriptorDatabase properly raises KeyError."""
    with patch('grpc_reflection.v1alpha.proto_reflection_descriptor_database.ServerReflectionStub'):
        mock_channel = Mock()
        db = ProtoReflectionDescriptorDatabase(mock_channel)
        
        # Mock a NOT_FOUND error response
        mock_response = Mock()
        mock_response.WhichOneof.return_value = "error_response"
        mock_response.error_response.error_code = grpc.StatusCode.NOT_FOUND.value[0]
        
        mock_stub = Mock()
        mock_stub.ServerReflectionInfo.return_value = iter([mock_response])
        db._stub = mock_stub
        
        # Test that KeyError is raised for not found items
        if key_type == 'string':
            with pytest.raises(KeyError) as exc_info:
                db.FindFileByName(key_value)
            assert key_value in str(exc_info.value)
        else:
            with pytest.raises(KeyError) as exc_info:
                db.FindFileContainingExtension(key_value, 100)
            assert key_value in str(exc_info.value) or "100" in str(exc_info.value)


# Test BaseReflectionServicer with None pool
def test_base_reflection_servicer_default_pool():
    """Test that BaseReflectionServicer uses default pool when None is provided."""
    from grpc_reflection.v1alpha._base import _POOL
    
    servicer = BaseReflectionServicer(['service1'], pool=None)
    assert servicer._pool is _POOL
    
    # With explicit pool
    custom_pool = Mock()
    servicer2 = BaseReflectionServicer(['service1'], pool=custom_pool)
    assert servicer2._pool is custom_pool


# Test for potential integer overflow in extension numbers
@given(
    extension_number=st.one_of(
        st.just(-2147483649),  # Below min int32
        st.just(2147483648),   # Above max int32
        st.just(0),
        st.just(-1),
        st.integers(min_value=-10**18, max_value=10**18)
    )
)
def test_extension_request_integer_bounds(extension_number):
    """Test ExtensionRequest with numbers outside typical int32 bounds."""
    try:
        request = reflection_pb2.ExtensionRequest(
            containing_type="test.Type",
            extension_number=extension_number
        )
        
        # Try to serialize
        serialized = request.SerializeToString()
        deserialized = reflection_pb2.ExtensionRequest()
        deserialized.ParseFromString(serialized)
        
        # If it succeeds, the value should be preserved or truncated consistently
        # Note: protobuf may truncate to int32 range
        note(f"Original: {extension_number}, Deserialized: {deserialized.extension_number}")
        
    except (ValueError, OverflowError) as e:
        # This is expected for values outside the valid range
        note(f"Expected error for {extension_number}: {e}")


# Test multiple simultaneous field settings in ServerReflectionRequest
def test_server_reflection_request_single_field_constraint():
    """Test that ServerReflectionRequest can only have one message_request field set."""
    request = reflection_pb2.ServerReflectionRequest()
    
    # Set file_by_filename
    request.file_by_filename = "test.proto"
    assert request.HasField("file_by_filename")
    assert request.WhichOneof("message_request") == "file_by_filename"
    
    # Setting another field should clear the first
    request.file_containing_symbol = "TestSymbol"
    assert request.HasField("file_containing_symbol")
    assert not request.HasField("file_by_filename")
    assert request.WhichOneof("message_request") == "file_containing_symbol"
    
    # Setting list_services should clear file_containing_symbol
    request.list_services = ""
    assert request.HasField("list_services")
    assert not request.HasField("file_containing_symbol")
    assert request.WhichOneof("message_request") == "list_services"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])