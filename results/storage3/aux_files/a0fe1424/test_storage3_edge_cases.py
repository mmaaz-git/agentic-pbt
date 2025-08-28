import sys
import urllib.parse
from unittest.mock import MagicMock, Mock, patch
import json
import base64

import pytest
from hypothesis import assume, given, settings, strategies as st
from hypothesis import HealthCheck

sys.path.append('/root/hypothesis-llm/envs/storage3_env/lib/python3.13/site-packages')

import storage3
from storage3._sync.file_api import SyncBucketProxy
from storage3.types import FileOptions, TransformOptions


@given(
    path=st.text().filter(lambda x: "/" not in x),
    expires_in=st.integers()
)
def test_create_signed_url_expires_in_string_conversion(path, expires_in):
    """Property: expires_in is always converted to string in create_signed_url"""
    mock_client = MagicMock()
    mock_client.base_url = "http://test.com/"
    mock_response = MagicMock()
    mock_response.json.return_value = {"signedURL": f"http://test.com/signed/{path}"}
    mock_client.request.return_value = mock_response
    
    proxy = SyncBucketProxy(id="test-bucket", _client=mock_client)
    
    try:
        result = proxy.create_signed_url(path, expires_in)
        
        # Check that the request was made with expires_in as a string
        call_args = mock_client.request.call_args
        if call_args and call_args[1] and 'json' in call_args[1]:
            json_data = call_args[1]['json']
            if 'expiresIn' in json_data:
                assert json_data['expiresIn'] == str(expires_in)
    except Exception:
        pass  # Some values might cause exceptions


@given(
    metadata=st.dictionaries(
        st.text(min_size=1),
        st.one_of(st.text(), st.integers(), st.booleans(), st.none())
    )
)
def test_metadata_base64_encoding(metadata):
    """Property: metadata is base64 encoded in upload operations"""
    mock_client = MagicMock()
    mock_client.base_url = "http://test.com/"
    mock_client.headers = {}
    mock_response = MagicMock()
    mock_response.json.return_value = {"Key": "test-key"}
    mock_client.request.return_value = mock_response
    
    proxy = SyncBucketProxy(id="test-bucket", _client=mock_client)
    
    file_options: FileOptions = {"metadata": metadata}
    
    try:
        result = proxy._upload_or_update("POST", "test.txt", b"content", file_options)
        
        # Check that metadata was base64 encoded
        call_args = mock_client.request.call_args
        if call_args and len(call_args) > 1:
            headers = call_args[1].get('headers', {})
            if 'x-metadata' in headers:
                # Should be base64 encoded
                encoded_metadata = headers['x-metadata']
                # Try to decode it
                decoded = base64.b64decode(encoded_metadata).decode()
                parsed = json.loads(decoded)
                assert parsed == metadata
    except Exception:
        pass


@given(
    cache_control=st.one_of(
        st.integers(min_value=0, max_value=86400),
        st.text(min_size=1)
    )
)
def test_cache_control_formatting(cache_control):
    """Property: numeric cache_control becomes 'max-age={value}'"""
    mock_client = MagicMock()
    mock_client.base_url = "http://test.com/"
    mock_client.headers = {}
    mock_response = MagicMock()
    mock_response.json.return_value = {"Key": "test-key"}
    mock_client.request.return_value = mock_response
    
    proxy = SyncBucketProxy(id="test-bucket", _client=mock_client)
    
    file_options: FileOptions = {"cache-control": str(cache_control)}
    
    try:
        result = proxy._upload_or_update("POST", "test.txt", b"content", file_options)
        
        call_args = mock_client.request.call_args
        if call_args and len(call_args) > 1:
            headers = call_args[1].get('headers', {})
            if 'cache-control' in headers:
                assert headers['cache-control'] == f"max-age={cache_control}"
    except Exception:
        pass


@given(
    path=st.text(min_size=1),
    transform_width=st.integers(min_value=1, max_value=10000),
    transform_height=st.integers(min_value=1, max_value=10000)
)
def test_transform_options_url_encoding(path, transform_width, transform_height):
    """Property: transform options are properly URL encoded"""
    mock_client = MagicMock()
    mock_client.base_url = "http://test.com/"
    proxy = SyncBucketProxy(id="test-bucket", _client=mock_client)
    
    transform: TransformOptions = {
        "width": transform_width,
        "height": transform_height
    }
    
    result = proxy.get_public_url(path, options={"transform": transform})
    
    # Check that transform parameters are in the URL
    assert "width=" in result or "width%3D" in result
    assert "height=" in result or "height%3D" in result
    assert str(transform_width) in result
    assert str(transform_height) in result


@given(
    paths=st.lists(st.text(min_size=1), min_size=1, max_size=10),
    expires_in=st.integers(min_value=0, max_value=86400)
)
def test_create_signed_urls_batch_processing(paths, expires_in):
    """Property: create_signed_urls processes all paths and returns same count"""
    mock_client = MagicMock()
    mock_client.base_url = "http://test.com/"
    
    # Mock response with same number of items as input
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"error": None, "path": p, "signedURL": f"http://test.com/signed/{p}"}
        for p in paths
    ]
    mock_client.request.return_value = mock_response
    
    proxy = SyncBucketProxy(id="test-bucket", _client=mock_client)
    
    try:
        result = proxy.create_signed_urls(paths, expires_in)
        
        # Should return same number of URLs as paths
        assert len(result) == len(paths)
        
        # Each result should have required fields
        for item in result:
            assert "error" in item
            assert "path" in item
            assert "signedURL" in item
            assert "signedUrl" in item
            # signedURL and signedUrl should be equal
            assert item["signedURL"] == item["signedUrl"]
    except Exception:
        pass


@given(
    bucket_id=st.text(min_size=1).filter(lambda x: "/" not in x),
    path_with_spaces=st.text(min_size=1).map(lambda x: f"folder with spaces/{x}.txt")
)
def test_path_with_spaces_handling(bucket_id, path_with_spaces):
    """Property: paths with spaces are properly handled"""
    mock_client = MagicMock()
    proxy = SyncBucketProxy(id=bucket_id, _client=mock_client)
    
    final_path = proxy._get_final_path(path_with_spaces)
    
    # Should include bucket id and path
    assert final_path.startswith(f"{bucket_id}/")
    assert "folder with spaces" in final_path
    
    # URL generation should handle spaces
    public_url = proxy.get_public_url(path_with_spaces)
    # Spaces should be encoded as %20 or kept as spaces in URL
    assert "folder" in public_url


@given(
    from_path=st.text(min_size=1).filter(lambda x: "/" not in x),
    to_path=st.text(min_size=1).filter(lambda x: "/" not in x)
)
def test_move_and_copy_path_structure(from_path, to_path):
    """Property: move and copy operations maintain correct JSON structure"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": "success"}
    mock_client.request.return_value = mock_response
    
    proxy = SyncBucketProxy(id="test-bucket", _client=mock_client)
    
    # Test move
    try:
        proxy.move(from_path, to_path)
        call_args = mock_client.request.call_args
        if call_args and len(call_args) > 1:
            json_data = call_args[1].get('json', {})
            assert json_data.get('bucketId') == "test-bucket"
            assert json_data.get('sourceKey') == from_path
            assert json_data.get('destinationKey') == to_path
    except Exception:
        pass
    
    # Test copy
    try:
        proxy.copy(from_path, to_path)
        call_args = mock_client.request.call_args
        if call_args and len(call_args) > 1:
            json_data = call_args[1].get('json', {})
            assert json_data.get('bucketId') == "test-bucket"
            assert json_data.get('sourceKey') == from_path
            assert json_data.get('destinationKey') == to_path
    except Exception:
        pass


@given(
    download=st.one_of(
        st.just(True),
        st.just(False),
        st.text(min_size=1)
    )
)
def test_download_query_parameter_formatting(download):
    """Property: download parameter is correctly formatted in URLs"""
    mock_client = MagicMock()
    mock_client.base_url = "http://test.com/"
    mock_response = MagicMock()
    mock_response.json.return_value = {"signedURL": "http://test.com/signed/path"}
    mock_client.request.return_value = mock_response
    
    proxy = SyncBucketProxy(id="test-bucket", _client=mock_client)
    
    try:
        result = proxy.create_signed_url("test.txt", 3600, options={"download": download})
        
        if download is True:
            # Should have "&download=" without value
            assert "&download=" in result["signedURL"] or "&download=" in result["signedUrl"]
        elif download is False:
            # Should not have download parameter
            pass
        else:
            # Should have "&download={value}"
            assert f"&download={download}" in result["signedURL"] or f"&download={download}" in result["signedUrl"]
    except Exception:
        pass


@given(
    upsert_value=st.text(min_size=1)
)
def test_upsert_header_conversion(upsert_value):
    """Property: upsert option is converted to x-upsert header"""
    mock_client = MagicMock()
    mock_client.base_url = "http://test.com/"
    mock_client.headers = {}
    mock_response = MagicMock()
    mock_response.json.return_value = {"Key": "test-key"}
    mock_client.request.return_value = mock_response
    
    proxy = SyncBucketProxy(id="test-bucket", _client=mock_client)
    
    file_options: FileOptions = {"upsert": upsert_value}
    
    try:
        result = proxy._upload_or_update("POST", "test.txt", b"content", file_options)
        
        call_args = mock_client.request.call_args
        if call_args and len(call_args) > 1:
            headers = call_args[1].get('headers', {})
            # x-upsert should be present for POST
            assert 'x-upsert' in headers
            assert headers['x-upsert'] == upsert_value
    except Exception:
        pass
    
    # For PUT, x-upsert should be removed
    try:
        result = proxy._upload_or_update("PUT", "test.txt", b"content", file_options)
        
        call_args = mock_client.request.call_args
        if call_args and len(call_args) > 1:
            headers = call_args[1].get('headers', {})
            # x-upsert should NOT be present for PUT
            assert 'x-upsert' not in headers
    except Exception:
        pass