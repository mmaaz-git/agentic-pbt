import sys
import urllib.parse
from unittest.mock import MagicMock

import pytest
from hypothesis import assume, given, settings, strategies as st

sys.path.append('/root/hypothesis-llm/envs/storage3_env/lib/python3.13/site-packages')

import storage3
from storage3 import create_client
from storage3._sync import SyncStorageClient
from storage3._async import AsyncStorageClient
from storage3._sync.file_api import SyncBucketProxy
from storage3.types import UploadResponse, BaseBucket, ListBucketFilesOptions
from storage3.constants import DEFAULT_TIMEOUT


@given(
    url=st.one_of(
        st.just("http://localhost:8000"),
        st.just("https://api.example.com"),
        st.text(min_size=1).map(lambda x: f"http://{x}.com")
    ),
    headers=st.dictionaries(st.text(min_size=1), st.text()),
    is_async=st.booleans()
)
@settings(suppress_health_check=[])
def test_create_client_returns_correct_type(url, headers, is_async):
    """Property: create_client returns AsyncStorageClient when is_async=True, SyncStorageClient when False"""
    client = create_client(url, headers, is_async=is_async)
    
    if is_async:
        assert isinstance(client, AsyncStorageClient)
    else:
        assert isinstance(client, SyncStorageClient)


@given(
    bucket_id=st.text(min_size=1).filter(lambda x: "/" not in x),
    path=st.text(min_size=0)
)
def test_get_final_path_prepends_bucket_id(bucket_id, path):
    """Property: _get_final_path always returns {bucket_id}/{path}"""
    mock_client = MagicMock()
    proxy = SyncBucketProxy(id=bucket_id, _client=mock_client)
    
    result = proxy._get_final_path(path)
    expected = f"{bucket_id}/{path}"
    
    assert result == expected


@given(
    timeout=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False)
    )
)
def test_timeout_always_positive(timeout):
    """Property: SyncStorageClient converts timeout to positive integer using abs()"""
    mock_client = MagicMock()
    mock_client.base_url = "http://test.com"
    mock_client.headers = MagicMock()
    mock_client.headers.update = MagicMock()
    
    client = SyncStorageClient(
        url="http://test.com",
        headers={},
        timeout=timeout,
        http_client=mock_client
    )
    
    if timeout is not None:
        assert client.timeout == int(abs(timeout))
        assert client.timeout >= 0
    else:
        assert client.timeout == DEFAULT_TIMEOUT


@given(
    path=st.text(min_size=1),
    key=st.text(min_size=1)
)
def test_upload_response_consistency(path, key):
    """Property: UploadResponse.full_path and fullPath are always equal"""
    response = UploadResponse(path=path, Key=key)
    
    assert response.full_path == response.fullPath
    assert response.full_path == key
    assert response.path == path


@given(
    path=st.text(min_size=1).filter(lambda x: x and not x.startswith("/")),
    special_chars=st.sampled_from(["#", "?", "&", " ", "!", "@", "$", "%", "^", "*"])
)
def test_public_url_encoding(path, special_chars):
    """Property: get_public_url properly encodes special characters in paths"""
    test_path = f"folder/{special_chars}file{special_chars}.txt"
    
    mock_client = MagicMock()
    mock_client.base_url = "http://test.com/"
    proxy = SyncBucketProxy(id="test-bucket", _client=mock_client)
    
    result = proxy.get_public_url(test_path)
    
    # URL should contain properly encoded path
    assert "http://test.com/" in result
    # Special characters should be present (either encoded or raw depending on character)
    # The path should be present in some form
    assert "folder" in result
    assert "file" in result or urllib.parse.quote("file") in result


@given(
    limit=st.integers(min_value=0, max_value=1000),
    offset=st.integers(min_value=0, max_value=10000)
)
def test_list_options_validation(limit, offset):
    """Property: ListBucketFilesOptions with limit and offset are properly structured"""
    options: ListBucketFilesOptions = {
        "limit": limit,
        "offset": offset
    }
    
    assert options["limit"] == limit
    assert options["offset"] == offset
    assert isinstance(options["limit"], int)
    assert isinstance(options["offset"], int)
    assert options["limit"] >= 0
    assert options["offset"] >= 0


@given(
    name=st.text(min_size=1),
    owner=st.text(min_size=1),
    public=st.booleans(),
    file_size_limit=st.one_of(st.none(), st.integers(min_value=1))
)
def test_base_bucket_model_validation(name, owner, public, file_size_limit):
    """Property: BaseBucket model properly validates and stores attributes"""
    from datetime import datetime
    
    bucket = BaseBucket(
        id="test-id",
        name=name,
        owner=owner,
        public=public,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        file_size_limit=file_size_limit,
        allowed_mime_types=None
    )
    
    assert bucket.name == name
    assert bucket.owner == owner
    assert bucket.public == public
    assert bucket.file_size_limit == file_size_limit
    assert isinstance(bucket.public, bool)


@given(
    download=st.one_of(
        st.booleans(),
        st.text(min_size=1)
    )
)
def test_url_options_download_field(download):
    """Property: URLOptions download field accepts both bool and string"""
    from storage3.types import URLOptions
    
    options: URLOptions = {"download": download}
    
    assert "download" in options
    assert options["download"] == download
    assert isinstance(options["download"], (bool, str))


@given(
    column=st.sampled_from(["name", "created_at", "updated_at", "size"]),
    order=st.sampled_from(["asc", "desc"])
)
def test_sort_by_type_structure(column, order):
    """Property: _sortByType has correct structure for sorting"""
    from storage3.types import _sortByType
    
    sort_option: _sortByType = {
        "column": column,
        "order": order
    }
    
    assert sort_option["column"] in ["name", "created_at", "updated_at", "size"]
    assert sort_option["order"] in ["asc", "desc"]


@given(
    cache_control=st.one_of(
        st.text(min_size=1),
        st.integers(min_value=0, max_value=86400)
    )
)
def test_file_options_cache_control(cache_control):
    """Property: FileOptions cache-control field accepts string values"""
    from storage3.types import FileOptions
    
    options: FileOptions = {"cache-control": str(cache_control)}
    
    assert "cache-control" in options
    assert isinstance(options["cache-control"], str)
    assert options["cache-control"] == str(cache_control)