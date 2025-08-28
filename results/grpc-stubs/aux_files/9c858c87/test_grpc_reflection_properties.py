#!/usr/bin/env python3
"""Property-based tests for grpc_reflection module using Hypothesis."""

import sys
import os

# Add the environment's site-packages to Python path
sys.path.insert(0, '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import pytest
from unittest.mock import Mock, MagicMock, patch
from google.protobuf import descriptor_pb2
from google.protobuf import descriptor_pool

# Import the modules to test
from grpc_reflection.v1alpha import reflection_pb2
from grpc_reflection.v1alpha import reflection_pb2_grpc
from grpc_reflection.v1alpha._base import BaseReflectionServicer, _collect_transitive_dependencies
from grpc_reflection.v1alpha.reflection import ReflectionServicer
from grpc_reflection.v1alpha.proto_reflection_descriptor_database import ProtoReflectionDescriptorDatabase
import grpc


# Strategy for generating valid protobuf field numbers
field_numbers = st.integers(min_value=1, max_value=536870911)  # Max field number in protobuf

# Strategy for generating valid protobuf names
proto_names = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_'),
    min_size=1,
    max_size=50
).filter(lambda x: x[0].isalpha() or x[0] == '_')

# Strategy for generating file paths - always end with .proto
@composite
def proto_file_paths(draw):
    name = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='/_-'),
        min_size=1, 
        max_size=50
    ))
    return name + '.proto'


# Test 1: Protobuf message serialization round-trip
@given(
    host=st.text(min_size=0, max_size=100),
    filename=proto_file_paths(),
    symbol=proto_names,
    extension_number=field_numbers
)
def test_server_reflection_request_round_trip(host, filename, symbol, extension_number):
    """Test that ServerReflectionRequest can be serialized and deserialized without data loss."""
    # Create request with various fields
    original = reflection_pb2.ServerReflectionRequest(
        host=host,
        file_by_filename=filename
    )
    
    # Serialize and deserialize
    serialized = original.SerializeToString()
    deserialized = reflection_pb2.ServerReflectionRequest()
    deserialized.ParseFromString(serialized)
    
    # Check round-trip preserves data
    assert deserialized.host == host
    assert deserialized.file_by_filename == filename


@given(
    containing_type=proto_names,
    extension_number=field_numbers
)
def test_extension_request_round_trip(containing_type, extension_number):
    """Test ExtensionRequest serialization round-trip."""
    original = reflection_pb2.ExtensionRequest(
        containing_type=containing_type,
        extension_number=extension_number
    )
    
    serialized = original.SerializeToString()
    deserialized = reflection_pb2.ExtensionRequest()
    deserialized.ParseFromString(serialized)
    
    assert deserialized.containing_type == containing_type
    assert deserialized.extension_number == extension_number


@given(
    error_code=st.integers(min_value=0, max_value=20),
    error_message=st.text(min_size=0, max_size=1000)
)
def test_error_response_round_trip(error_code, error_message):
    """Test ErrorResponse serialization round-trip."""
    original = reflection_pb2.ErrorResponse(
        error_code=error_code,
        error_message=error_message
    )
    
    serialized = original.SerializeToString()
    deserialized = reflection_pb2.ErrorResponse()
    deserialized.ParseFromString(serialized)
    
    assert deserialized.error_code == error_code
    assert deserialized.error_message == error_message


# Test 2: BaseReflectionServicer service names invariant
@given(
    service_names=st.lists(proto_names, min_size=0, max_size=10)
)
def test_base_reflection_servicer_sorted_invariant(service_names):
    """Test that BaseReflectionServicer maintains sorted service names."""
    servicer = BaseReflectionServicer(service_names)
    
    # Service names should be sorted
    assert servicer._service_names == tuple(sorted(service_names))
    
    # Service names should be immutable (tuple)
    assert isinstance(servicer._service_names, tuple)


@given(
    service_names=st.lists(proto_names, min_size=1, max_size=5)
)
def test_list_services_response_consistency(service_names):
    """Test that _list_services returns all registered services."""
    servicer = BaseReflectionServicer(service_names)
    request = reflection_pb2.ServerReflectionRequest()
    
    response = servicer._list_services(request)
    
    # Response should contain all services
    assert response.HasField('list_services_response')
    returned_names = [s.name for s in response.list_services_response.service]
    assert set(returned_names) == set(service_names)
    assert returned_names == sorted(service_names)


# Test 3: File descriptor collection properties
def test_collect_transitive_dependencies_no_cycles():
    """Test that _collect_transitive_dependencies handles dependency graphs correctly."""
    # Create mock file descriptors with dependencies
    file1 = Mock()
    file1.name = "file1.proto"
    file1.dependencies = []
    
    file2 = Mock()
    file2.name = "file2.proto"
    file2.dependencies = [file1]
    
    file3 = Mock()
    file3.name = "file3.proto"
    file3.dependencies = [file2, file1]
    
    seen_files = {}
    _collect_transitive_dependencies(file3, seen_files)
    
    # All files should be collected
    assert len(seen_files) == 3
    assert "file1.proto" in seen_files
    assert "file2.proto" in seen_files
    assert "file3.proto" in seen_files


@given(
    num_dependencies=st.integers(min_value=0, max_value=10)
)
def test_collect_dependencies_idempotent(num_dependencies):
    """Test that collecting dependencies multiple times gives same result."""
    # Create a chain of dependencies
    files = []
    for i in range(num_dependencies + 1):
        f = Mock()
        f.name = f"file{i}.proto"
        f.dependencies = files[:i]  # Each file depends on all previous
        files.append(f)
    
    if files:
        root = files[-1]
        
        # Collect dependencies twice
        seen1 = {}
        _collect_transitive_dependencies(root, seen1)
        
        seen2 = {}
        _collect_transitive_dependencies(root, seen2)
        
        # Should get same result
        assert set(seen1.keys()) == set(seen2.keys())
        assert len(seen1) == len(files)


# Test 4: ProtoReflectionDescriptorDatabase consistency
@given(
    file_names=st.lists(proto_file_paths(), min_size=1, max_size=5, unique=True)
)
def test_proto_reflection_db_known_files_monotonic(file_names):
    """Test that _known_files only grows, never shrinks."""
    with patch('grpc_reflection.v1alpha.proto_reflection_descriptor_database.ServerReflectionStub'):
        mock_channel = Mock()
        db = ProtoReflectionDescriptorDatabase(mock_channel)
        
        initial_size = len(db._known_files)
        
        # Add files one by one
        for i, name in enumerate(file_names):
            # Mock the file descriptor
            desc = descriptor_pb2.FileDescriptorProto()
            desc.name = name
            
            # Add to known files
            db._known_files.add(name)
            db.Add(desc)
            
            # Known files should only grow
            assert len(db._known_files) >= initial_size + i + 1
            assert name in db._known_files


@given(
    extendee_name=proto_names,
    extension_numbers=st.lists(field_numbers, min_size=1, max_size=10, unique=True)
)
def test_cached_extension_numbers_consistency(extendee_name, extension_numbers):
    """Test that cached extension numbers remain consistent."""
    with patch('grpc_reflection.v1alpha.proto_reflection_descriptor_database.ServerReflectionStub'):
        mock_channel = Mock()
        db = ProtoReflectionDescriptorDatabase(mock_channel)
        
        # Mock the response
        mock_response = Mock()
        mock_response.all_extension_numbers_response.extension_number = extension_numbers
        mock_response.WhichOneof.return_value = "all_extension_numbers_response"
        
        mock_stub = Mock()
        mock_stub.ServerReflectionInfo.return_value = iter([mock_response])
        db._stub = mock_stub
        
        # First call should cache
        result1 = db.FindAllExtensionNumbers(extendee_name)
        
        # Second call should return cached value (no new server call)
        result2 = db.FindAllExtensionNumbers(extendee_name)
        
        # Results should be identical
        assert list(result1) == list(result2)
        assert list(result1) == extension_numbers


# Test 5: Error handling properties
@given(
    error_code=st.integers(min_value=0, max_value=16),
    request_type=st.sampled_from(['file_by_filename', 'file_containing_symbol', 'list_services'])
)
def test_error_response_preserves_original_request(error_code, request_type):
    """Test that error responses preserve the original request."""
    from grpc_reflection.v1alpha._base import _not_found_error
    
    # Create different types of requests
    if request_type == 'file_by_filename':
        request = reflection_pb2.ServerReflectionRequest(file_by_filename="test.proto")
    elif request_type == 'file_containing_symbol':
        request = reflection_pb2.ServerReflectionRequest(file_containing_symbol="TestMessage")
    else:
        request = reflection_pb2.ServerReflectionRequest(list_services="")
    
    # Generate error response
    error_response = _not_found_error(request)
    
    # Original request should be preserved
    assert error_response.original_request == request
    assert error_response.HasField('error_response')
    assert error_response.error_response.error_code == grpc.StatusCode.NOT_FOUND.value[0]


# Test 6: Request validation
def test_reflection_servicer_handles_empty_request():
    """Test that ReflectionServicer handles requests with no fields set."""
    servicer = ReflectionServicer([])
    request = reflection_pb2.ServerReflectionRequest()
    context = Mock()
    
    # Process empty request
    responses = list(servicer.ServerReflectionInfo(iter([request]), context))
    
    # Should return error for invalid request
    assert len(responses) == 1
    assert responses[0].HasField('error_response')
    assert responses[0].error_response.error_code == grpc.StatusCode.INVALID_ARGUMENT.value[0]


@given(
    service_names=st.lists(proto_names, min_size=0, max_size=5)
)
def test_reflection_servicer_list_services(service_names):
    """Test that listing services works correctly."""
    servicer = ReflectionServicer(service_names)
    request = reflection_pb2.ServerReflectionRequest(list_services="")
    context = Mock()
    
    responses = list(servicer.ServerReflectionInfo(iter([request]), context))
    
    assert len(responses) == 1
    assert responses[0].HasField('list_services_response')
    returned_names = [s.name for s in responses[0].list_services_response.service]
    assert set(returned_names) == set(service_names)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])