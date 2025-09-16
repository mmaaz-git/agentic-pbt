#!/usr/bin/env python3
"""Property-based tests for storage3.types module."""

import sys
import json
from datetime import datetime
from typing import Any, Dict

import hypothesis.strategies as st
from hypothesis import given, settings, assume
import pytest

# Add the storage3 environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/storage3_env/lib/python3.13/site-packages')

from storage3.types import (
    UploadResponse,
    BaseBucket,
    SignedUrlResponse,
    CreateSignedUrlResponse,
    SignedUploadURL
)


# Strategy for generating test strings
text_strategy = st.text(min_size=1, max_size=100)
path_strategy = st.text(alphabet=st.characters(blacklist_characters="\x00\n\r"), min_size=1, max_size=200)


@given(
    path=path_strategy,
    key=st.one_of(st.none(), path_strategy)
)
def test_upload_response_initialization_and_serialization(path, key):
    """Test UploadResponse dataclass/init conflict and dict conversion.
    
    UploadResponse has both @dataclass decorator and custom __init__.
    This tests whether the class works correctly with its conflicting definitions.
    """
    
    # Test instantiation with the custom __init__ signature
    response = UploadResponse(path=path, Key=key)
    
    # Check that all fields are set correctly
    assert response.path == path
    assert response.full_path == key
    assert response.fullPath == key
    
    # Test the dict conversion using the assigned asdict method
    try:
        result_dict = response.dict()
        
        # The dataclass asdict should include all three fields
        assert 'path' in result_dict
        assert 'full_path' in result_dict
        assert 'fullPath' in result_dict
        
        # Check values match
        assert result_dict['path'] == path
        assert result_dict['full_path'] == key
        assert result_dict['fullPath'] == key
        
    except Exception as e:
        # This might fail due to the dataclass/init conflict
        pytest.fail(f"dict() method failed: {e}")


@given(
    path=path_strategy,
    full_path=path_strategy,
    fullPath=path_strategy
)
def test_upload_response_dataclass_constructor(path, full_path, fullPath):
    """Test if UploadResponse can be instantiated as a regular dataclass.
    
    Since it's decorated with @dataclass, it should support the dataclass constructor,
    but the custom __init__ overrides this.
    """
    
    # Try to instantiate using dataclass-style constructor
    # This should fail because the custom __init__ expects different parameters
    with pytest.raises(TypeError):
        # This should fail because __init__ expects (path, Key) not (path, full_path, fullPath)
        response = UploadResponse(path=path, full_path=full_path, fullPath=fullPath)


@given(
    id=text_strategy,
    name=text_strategy,
    owner=text_strategy,
    public=st.booleans(),
    created_at=st.datetimes(),
    updated_at=st.datetimes(),
    file_size_limit=st.one_of(st.none(), st.integers(min_value=0, max_value=10**12)),
    allowed_mime_types=st.one_of(st.none(), st.lists(text_strategy, min_size=0, max_size=10))
)
def test_base_bucket_pydantic_model(id, name, owner, public, created_at, updated_at, file_size_limit, allowed_mime_types):
    """Test BaseBucket Pydantic model validation and serialization."""
    
    # Create a BaseBucket instance
    bucket = BaseBucket(
        id=id,
        name=name,
        owner=owner,
        public=public,
        created_at=created_at,
        updated_at=updated_at,
        file_size_limit=file_size_limit,
        allowed_mime_types=allowed_mime_types
    )
    
    # Test that all fields are set correctly
    assert bucket.id == id
    assert bucket.name == name
    assert bucket.owner == owner
    assert bucket.public == public
    assert bucket.created_at == created_at
    assert bucket.updated_at == updated_at
    assert bucket.file_size_limit == file_size_limit
    assert bucket.allowed_mime_types == allowed_mime_types
    
    # Test model_dump (Pydantic v2) or dict (Pydantic v1)
    if hasattr(bucket, 'model_dump'):
        bucket_dict = bucket.model_dump()
    else:
        bucket_dict = bucket.dict()
    
    # Verify round-trip: dict -> model -> dict
    bucket2 = BaseBucket(**bucket_dict)
    if hasattr(bucket2, 'model_dump'):
        bucket2_dict = bucket2.model_dump()
    else:
        bucket2_dict = bucket2.dict()
    
    # Compare the dictionaries (accounting for datetime serialization)
    for key in bucket_dict:
        if isinstance(bucket_dict[key], datetime):
            # Datetime comparison might have microsecond differences after serialization
            assert bucket2_dict[key] == bucket_dict[key]
        else:
            assert bucket2_dict[key] == bucket_dict[key]


@given(
    signed_url=text_strategy,
    token=text_strategy,
    path=path_strategy
)
def test_signed_upload_url_dual_fields(signed_url, token, path):
    """Test SignedUploadURL TypedDict with duplicate snake_case/camelCase fields.
    
    SignedUploadURL has both 'signed_url' and 'signedUrl' fields.
    This tests whether both naming conventions are handled correctly.
    """
    
    # Create a dictionary with both field naming conventions
    upload_url: SignedUploadURL = {
        'signed_url': signed_url,
        'signedUrl': signed_url,  # Same value for consistency
        'token': token,
        'path': path
    }
    
    # Both fields should be accessible
    assert upload_url['signed_url'] == signed_url
    assert upload_url['signedUrl'] == signed_url
    assert upload_url['token'] == token
    assert upload_url['path'] == path
    
    # Test with different values for the duplicate fields
    upload_url2: SignedUploadURL = {
        'signed_url': signed_url + "_snake",
        'signedUrl': signed_url + "_camel",
        'token': token,
        'path': path
    }
    
    # Fields should maintain their independent values
    assert upload_url2['signed_url'] == signed_url + "_snake"
    assert upload_url2['signedUrl'] == signed_url + "_camel"


@given(
    error=st.one_of(st.none(), text_strategy),
    path=path_strategy,
    signed_url=text_strategy
)
def test_create_signed_url_response_dual_fields(error, path, signed_url):
    """Test CreateSignedUrlResponse TypedDict with duplicate fields."""
    
    response: CreateSignedUrlResponse = {
        'error': error,
        'path': path,
        'signedURL': signed_url,
        'signedUrl': signed_url
    }
    
    # All fields should be accessible
    assert response['error'] == error
    assert response['path'] == path
    assert response['signedURL'] == signed_url
    assert response['signedUrl'] == signed_url


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])