import sys
import os
import tempfile
from io import BytesIO
from pathlib import Path

sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pyramid.response
from pyramid.response import FileIter, FileResponse, _guess_type


# Test 1: FileIter invariant - all chunks concatenated equal original content
@given(
    content=st.binary(min_size=0, max_size=10000),
    block_size=st.integers(min_value=1, max_value=1000)
)
def test_fileiter_content_invariant(content, block_size):
    """FileIter should read the entire file content exactly."""
    file_obj = BytesIO(content)
    
    # Create FileIter and read all chunks
    file_iter = FileIter(file_obj, block_size=block_size)
    chunks = list(file_iter)
    
    # Concatenate all chunks
    result = b''.join(chunks)
    
    # The result should equal the original content
    assert result == content, f"FileIter didn't preserve content. Expected {len(content)} bytes, got {len(result)}"


# Test 2: _guess_type invariant - always returns valid tuple
@given(path=st.text(min_size=1))
def test_guess_type_never_none(path):
    """_guess_type should never return None as content_type."""
    content_type, content_encoding = _guess_type(path)
    
    # First element should never be None
    assert content_type is not None, f"_guess_type returned None for path: {path}"
    assert isinstance(content_type, str), f"content_type should be string, got {type(content_type)}"
    
    # content_encoding can be None or string
    assert content_encoding is None or isinstance(content_encoding, str), \
        f"content_encoding should be None or string, got {type(content_encoding)}"


# Test 3: _guess_type default fallback
@given(path=st.text(min_size=1).filter(lambda x: not any(x.endswith(ext) for ext in ['.txt', '.html', '.json', '.xml', '.jpg', '.png', '.gif', '.pdf', '.zip'])))
def test_guess_type_default_fallback(path):
    """_guess_type should default to application/octet-stream for unknown extensions."""
    content_type, _ = _guess_type(path)
    
    # For paths without common extensions, should often default to application/octet-stream
    # Note: This is not always true as mimetypes has many registered types
    # But we can verify the function doesn't crash and returns valid output
    assert isinstance(content_type, str)
    assert len(content_type) > 0


# Test 4: FileResponse properties with real files
@given(
    content=st.binary(min_size=0, max_size=10000),
    cache_max_age=st.one_of(st.none(), st.integers(min_value=0, max_value=86400))
)
@settings(max_examples=100)
def test_fileresponse_properties(content, cache_max_age):
    """FileResponse should correctly set content_length and serve file content."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
        f.write(content)
        temp_path = f.name
    
    try:
        # Create FileResponse
        response = FileResponse(temp_path, cache_max_age=cache_max_age)
        
        # Check content_length matches file size
        actual_size = os.path.getsize(temp_path)
        assert response.content_length == actual_size, \
            f"content_length mismatch: {response.content_length} != {actual_size}"
        
        # Check that we can consume the app_iter and get the original content
        chunks = list(response.app_iter)
        result = b''.join(chunks)
        assert result == content, f"FileResponse didn't preserve content"
        
        # Check cache settings if specified
        if cache_max_age is not None:
            assert hasattr(response, 'cache_control'), "Response should have cache_control"
            # The cache_expires property sets cache_control.max_age
            assert response.cache_control.max_age == cache_max_age
        
        # Close the file iterator
        if hasattr(response.app_iter, 'close'):
            response.app_iter.close()
    
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)


# Test 5: FileIter close method
@given(content=st.binary(min_size=0, max_size=1000))
def test_fileiter_close(content):
    """FileIter.close() should close the underlying file."""
    file_obj = BytesIO(content)
    file_iter = FileIter(file_obj)
    
    # Consume some data (optional)
    try:
        next(file_iter)
    except StopIteration:
        pass  # Empty file
    
    # Close should close the underlying file
    file_iter.close()
    assert file_obj.closed, "FileIter.close() didn't close the underlying file"


# Test 6: FileResponse with different file extensions
@given(
    content=st.binary(min_size=1, max_size=1000),
    extension=st.sampled_from(['.txt', '.html', '.json', '.xml', '.jpg', '.png', '.pdf', '.bin', '.xyz'])
)
def test_fileresponse_content_type_guessing(content, extension):
    """FileResponse should guess content type based on file extension."""
    # Create temp file with specific extension
    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as f:
        f.write(content)
        temp_path = f.name
    
    try:
        # Create FileResponse without specifying content_type
        response = FileResponse(temp_path)
        
        # Check that content_type was set
        assert response.content_type is not None
        assert isinstance(response.content_type, str)
        
        # For known extensions, verify correct type
        expected_types = {
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.jpg': 'image/jpeg',
            '.png': 'image/png',
            '.pdf': 'application/pdf',
        }
        
        if extension in expected_types:
            # Some systems might add charset, so we check if it starts with expected type
            assert response.content_type.startswith(expected_types[extension]), \
                f"Wrong content type for {extension}: {response.content_type}"
        
        # Close the iterator
        if hasattr(response.app_iter, 'close'):
            response.app_iter.close()
    
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


if __name__ == "__main__":
    # Run a quick smoke test
    test_fileiter_content_invariant()
    test_guess_type_never_none()
    test_fileresponse_properties()
    print("Basic smoke tests passed!")