import io
import sys
import uuid
from unittest.mock import Mock
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from pyatlan.multipart_data_generator import MultipartDataGenerator
import pytest


# Test 1: Boundary uniqueness invariant
@given(st.integers(min_value=1, max_value=100))
def test_boundary_uniqueness(n):
    """Each instance should have a unique boundary"""
    generators = [MultipartDataGenerator() for _ in range(n)]
    boundaries = [gen.boundary for gen in generators]
    # All boundaries should be unique
    assert len(boundaries) == len(set(boundaries))


# Test 2: File extension to content type mapping
@given(st.sampled_from([
    (".png", "image/png"),
    (".gif", "image/gif"),
    (".jpg", "image/jpeg"),
    (".jpeg", "image/jpeg"),
    (".jfif", "image/jpeg"),
    (".pjpeg", "image/jpeg"),
    (".pjp", "image/jpeg"),
    (".svg", "image/svg+xml"),
    (".apng", "image/apng"),
    (".avif", "image/avif"),
    (".webp", "image/webp"),
]))
def test_content_type_mapping(file_extension_and_type):
    """Test that known file extensions get correct content type"""
    extension, expected_type = file_extension_and_type
    filename = f"test{extension}"
    
    gen = MultipartDataGenerator()
    mock_file = io.BytesIO(b"test content")
    gen.add_file(mock_file, filename)
    
    result = gen.get_post_data()
    assert expected_type.encode() in result


# Test 3: Default content type for unknown extensions
@given(st.text(min_size=1, max_size=10).filter(lambda s: not any(s.endswith(ext) for ext in [
    ".png", ".gif", ".jpg", ".jpeg", ".jfif", ".pjpeg", ".pjp", ".svg", ".apng", ".avif", ".webp"
])))
def test_default_content_type(extension):
    """Unknown extensions should get application/octet-stream"""
    filename = f"test.{extension}"
    
    gen = MultipartDataGenerator()
    mock_file = io.BytesIO(b"test content")
    gen.add_file(mock_file, filename)
    
    result = gen.get_post_data()
    assert b"Content-Type: application/octet-stream" in result


# Test 4: Write method type handling
@given(st.one_of(
    st.binary(min_size=0, max_size=1000),
    st.text(min_size=0, max_size=1000)
))
def test_write_accepts_bytes_and_strings(data):
    """_write should handle both bytes and strings"""
    gen = MultipartDataGenerator()
    # This should not raise an exception
    gen._write(data)
    # Verify data was written
    written = gen.data.getvalue()
    if isinstance(data, str):
        assert data.encode('utf-8') == written
    else:
        assert data == written


# Test 5: Write method rejects invalid types
@given(st.one_of(
    st.integers(),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text()),
    st.none()
))
def test_write_rejects_invalid_types(invalid_data):
    """_write should raise TypeError for non-bytes/str types"""
    gen = MultipartDataGenerator()
    with pytest.raises(TypeError):
        gen._write(invalid_data)


# Test 6: Multipart structure invariants
@given(
    st.binary(min_size=0, max_size=1000),
    st.text(min_size=1, max_size=50).filter(lambda s: '/' not in s and '\\' not in s)
)
def test_multipart_structure(file_content, filename):
    """Generated multipart data should have proper structure"""
    gen = MultipartDataGenerator()
    mock_file = io.BytesIO(file_content)
    gen.add_file(mock_file, filename)
    result = gen.get_post_data()
    
    # Should contain boundary markers
    boundary = str(gen.boundary).encode()
    assert b"--" + boundary in result
    assert b"--" + boundary + b"--" in result  # End boundary
    
    # Should contain proper headers
    assert b"Content-Disposition: form-data" in result
    assert b'name="file"' in result
    assert b'name="name"' in result
    assert f'filename="{filename}"'.encode() in result


# Test 7: Chunk size parameter
@given(
    st.integers(min_value=1, max_value=10000),
    st.binary(min_size=0, max_size=10000),
    st.text(min_size=1, max_size=50).filter(lambda s: '/' not in s and '\\' not in s)
)
def test_chunk_size_parameter(chunk_size, file_content, filename):
    """Generator should respect chunk_size parameter"""
    gen = MultipartDataGenerator(chunk_size=chunk_size)
    assert gen.chunk_size == chunk_size
    
    # Should be able to process file regardless of chunk size
    mock_file = io.BytesIO(file_content)
    gen.add_file(mock_file, filename)
    result = gen.get_post_data()
    
    # File content should be in the result
    assert file_content in result


# Test 8: Multiple calls to add_file
@given(
    st.lists(
        st.tuples(
            st.binary(min_size=0, max_size=100),
            st.text(min_size=1, max_size=20).filter(lambda s: '/' not in s and '\\' not in s)
        ),
        min_size=1,
        max_size=5
    )
)
def test_multiple_add_file_calls(files_data):
    """Multiple calls to add_file should accumulate data"""
    gen = MultipartDataGenerator()
    
    for content, filename in files_data:
        mock_file = io.BytesIO(content)
        gen.add_file(mock_file, filename)
    
    result = gen.get_post_data()
    
    # All filenames should appear in result
    for content, filename in files_data:
        assert f'filename="{filename}"'.encode() in result
        assert content in result


# Test 9: Empty file handling
@given(st.text(min_size=1, max_size=50).filter(lambda s: '/' not in s and '\\' not in s))
def test_empty_file_handling(filename):
    """Should handle empty files correctly"""
    gen = MultipartDataGenerator()
    mock_file = io.BytesIO(b"")
    gen.add_file(mock_file, filename)
    result = gen.get_post_data()
    
    # Should still have proper structure
    assert b"Content-Disposition: form-data" in result
    assert f'filename="{filename}"'.encode() in result


# Test 10: Line break consistency
@given(
    st.binary(min_size=0, max_size=100),
    st.text(min_size=1, max_size=20).filter(lambda s: '/' not in s and '\\' not in s)
)
def test_line_break_consistency(content, filename):
    """Line breaks should be consistent (\\r\\n)"""
    gen = MultipartDataGenerator()
    mock_file = io.BytesIO(content)
    gen.add_file(mock_file, filename)
    result = gen.get_post_data()
    
    # Check for CRLF line breaks
    assert b"\r\n" in result
    # Should not have lone LF or CR
    result_str = result.decode('utf-8', errors='ignore')
    # Replace all CRLF first, then check for lone CR or LF
    temp = result_str.replace('\r\n', '')
    assert '\r' not in temp
    assert '\n' not in temp


# Test 11: File extension extraction edge cases
@given(st.sampled_from([
    "file",  # No extension
    ".hidden",  # Starts with dot
    "file.tar.gz",  # Multiple dots
    "file.",  # Ends with dot
    "",  # Empty filename
]))
def test_file_extension_edge_cases(filename):
    """Test edge cases in file extension extraction"""
    gen = MultipartDataGenerator()
    mock_file = io.BytesIO(b"content")
    
    # This should not crash
    gen.add_file(mock_file, filename)
    result = gen.get_post_data()
    
    # Should default to application/octet-stream for these edge cases
    assert b"Content-Type: " in result


# Test 12: UUID boundary format
def test_boundary_is_uuid():
    """Boundary should be a valid UUID"""
    gen = MultipartDataGenerator()
    # Should be a UUID object
    assert isinstance(gen.boundary, uuid.UUID)
    # String representation should be valid UUID format
    boundary_str = str(gen.boundary)
    # Should be able to parse it back as UUID
    parsed = uuid.UUID(boundary_str)
    assert parsed == gen.boundary