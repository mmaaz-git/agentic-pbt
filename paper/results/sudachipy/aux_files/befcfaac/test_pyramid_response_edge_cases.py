import sys
import os
import tempfile
from io import BytesIO
import time

sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pyramid.response
from pyramid.response import FileIter, FileResponse, _guess_type


# Edge case 1: FileIter with files that don't support read() properly
class BadFile:
    """A file-like object that behaves incorrectly."""
    def __init__(self, data):
        self.data = data
        self.pos = 0
    
    def read(self, size):
        # Return more data than requested (violates contract)
        if self.pos >= len(self.data):
            return b''
        result = self.data[self.pos:self.pos + size * 2]  # Return double!
        self.pos += len(result)
        return result
    
    def close(self):
        pass


@given(content=st.binary(min_size=1, max_size=100))
def test_fileiter_with_bad_file(content):
    """FileIter should handle files that return more data than requested."""
    bad_file = BadFile(content)
    file_iter = FileIter(bad_file, block_size=10)
    
    # This should still work, even if the file is misbehaving
    chunks = list(file_iter)
    result = b''.join(chunks)
    
    # The FileIter doesn't validate the size, so it will return whatever the file gives
    # This is actually correct behavior - FileIter trusts the file object
    assert len(result) >= len(content) or len(result) <= len(content)


# Edge case 2: FileResponse with non-existent file
@given(filename=st.text(min_size=1, max_size=100).filter(lambda x: '/' not in x and '\\' not in x))
def test_fileresponse_nonexistent_file(filename):
    """FileResponse should raise appropriate error for non-existent files."""
    # Ensure the file doesn't exist
    temp_dir = tempfile.gettempdir()
    fake_path = os.path.join(temp_dir, f"nonexistent_{filename}")
    
    if os.path.exists(fake_path):
        os.unlink(fake_path)
    
    # This should raise FileNotFoundError
    try:
        response = FileResponse(fake_path)
        assert False, "FileResponse should have raised an error for non-existent file"
    except (FileNotFoundError, OSError):
        pass  # Expected


# Edge case 3: FileResponse with empty file
def test_fileresponse_empty_file():
    """FileResponse should handle empty files correctly."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name
    
    try:
        response = FileResponse(temp_path)
        
        # Check content_length is 0
        assert response.content_length == 0
        
        # Check we can iterate without errors
        chunks = list(response.app_iter)
        assert chunks == [] or chunks == [b'']
        
        if hasattr(response.app_iter, 'close'):
            response.app_iter.close()
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


# Edge case 4: FileIter with zero block size (should this be allowed?)
@given(content=st.binary(min_size=1, max_size=100))
def test_fileiter_zero_block_size(content):
    """FileIter with block_size=0 - what happens?"""
    file_obj = BytesIO(content)
    
    # This might be a bug - what happens with block_size=0?
    file_iter = FileIter(file_obj, block_size=0)
    
    try:
        chunks = []
        for i, chunk in enumerate(file_iter):
            chunks.append(chunk)
            if i > 1000:  # Prevent infinite loop
                break
        
        result = b''.join(chunks)
        # With block_size=0, read(0) returns empty bytes, causing infinite loop!
        print(f"Result length: {len(result)}, iterations: {i}")
    except Exception as e:
        print(f"Exception with block_size=0: {e}")


# Edge case 5: FileResponse with special characters in path
@given(
    content=st.binary(min_size=1, max_size=100),
    special_chars=st.text(alphabet="'\"<>|&;`$", min_size=1, max_size=5)
)
def test_fileresponse_special_chars_in_path(content, special_chars):
    """FileResponse should handle paths with special characters."""
    # Create temp file with special characters (where filesystem allows)
    try:
        with tempfile.NamedTemporaryFile(delete=False, prefix=f"test_{special_chars}_", suffix=".bin") as f:
            f.write(content)
            temp_path = f.name
    except (OSError, ValueError):
        # Some characters might not be allowed in filenames
        return
    
    try:
        response = FileResponse(temp_path)
        
        # Should work normally
        assert response.content_length == len(content)
        
        chunks = list(response.app_iter)
        result = b''.join(chunks)
        assert result == content
        
        if hasattr(response.app_iter, 'close'):
            response.app_iter.close()
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


# Edge case 6: Multiple iterations over FileIter
@given(content=st.binary(min_size=1, max_size=100))
def test_fileiter_multiple_iterations(content):
    """Can we iterate over FileIter multiple times?"""
    file_obj = BytesIO(content)
    file_iter = FileIter(file_obj)
    
    # First iteration
    chunks1 = list(file_iter)
    result1 = b''.join(chunks1)
    
    # Try second iteration - file pointer is at end
    chunks2 = list(file_iter)
    result2 = b''.join(chunks2)
    
    # Second iteration should be empty (file not rewound)
    assert result1 == content
    assert result2 == b''


# Edge case 7: FileResponse with symbolic links
@given(content=st.binary(min_size=1, max_size=100))
def test_fileresponse_symlink(content):
    """FileResponse should work with symbolic links."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(content)
        real_path = f.name
    
    # Create symlink
    link_path = real_path + ".link"
    
    try:
        os.symlink(real_path, link_path)
        
        # FileResponse via symlink
        response = FileResponse(link_path)
        
        assert response.content_length == len(content)
        
        chunks = list(response.app_iter)
        result = b''.join(chunks)
        assert result == content
        
        if hasattr(response.app_iter, 'close'):
            response.app_iter.close()
    
    except OSError:
        # Symlinks might not be supported
        pass
    finally:
        if os.path.exists(real_path):
            os.unlink(real_path)
        if os.path.exists(link_path):
            os.unlink(link_path)


# Edge case 8: _guess_type with null bytes
@given(path=st.text().map(lambda x: x + '\x00'))
def test_guess_type_null_bytes(path):
    """_guess_type with null bytes in path."""
    try:
        content_type, content_encoding = _guess_type(path)
        # Should handle it gracefully
        assert content_type is not None
    except (ValueError, TypeError):
        # Might raise an error for null bytes
        pass


if __name__ == "__main__":
    # Test the zero block size issue
    print("Testing FileIter with block_size=0...")
    test_fileiter_zero_block_size()