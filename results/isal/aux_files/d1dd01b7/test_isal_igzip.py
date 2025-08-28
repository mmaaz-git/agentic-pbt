"""Property-based tests for isal.igzip module using Hypothesis."""

import io
import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume, HealthCheck
import isal.igzip as igzip
import isal.igzip_lib as igzip_lib
import isal.isal_zlib as isal_zlib


# Test 1: Round-trip property - decompress(compress(x)) = x
@given(st.binary(min_size=0))
@settings(max_examples=100)
def test_compress_decompress_round_trip(data):
    """Test that compress/decompress is a perfect round-trip for any binary data."""
    compressed = igzip.compress(data)
    decompressed = igzip.decompress(compressed)
    assert decompressed == data


# Test 2: All compression levels produce valid compressed data
@given(
    st.binary(min_size=0),
    st.integers(min_value=isal_zlib.ISAL_BEST_SPEED, 
                max_value=isal_zlib.ISAL_BEST_COMPRESSION)
)
@settings(max_examples=50)
def test_compression_levels_all_valid(data, level):
    """Test that all compression levels produce valid compressed data."""
    compressed = igzip.compress(data, compresslevel=level)
    decompressed = igzip.decompress(compressed)
    assert decompressed == data


# Test 3: Compression with mtime parameter
@given(
    st.binary(min_size=0),
    st.integers(min_value=0, max_value=2**32 - 1)  # Valid Unix timestamp range
)
@settings(max_examples=20)
def test_compress_with_mtime(data, mtime):
    """Test that compress with mtime parameter works correctly."""
    compressed = igzip.compress(data, mtime=mtime)
    decompressed = igzip.decompress(compressed)
    assert decompressed == data


# Test 4: IGzipFile write/read round-trip
@given(st.binary(min_size=0))
@settings(max_examples=50)
def test_igzipfile_write_read_round_trip(data):
    """Test that IGzipFile can write and read back the same data."""
    buffer = io.BytesIO()
    
    # Write compressed data
    with igzip.IGzipFile(mode='wb', fileobj=buffer) as f:
        f.write(data)
    
    # Read back compressed data
    buffer.seek(0)
    with igzip.IGzipFile(mode='rb', fileobj=buffer) as f:
        decompressed = f.read()
    
    assert decompressed == data


# Test 5: Multiple writes to IGzipFile
@given(st.lists(st.binary(min_size=0), min_size=0, max_size=10))
@settings(max_examples=30)
def test_igzipfile_multiple_writes(data_list):
    """Test that multiple writes to IGzipFile are correctly handled."""
    buffer = io.BytesIO()
    
    # Write multiple chunks
    with igzip.IGzipFile(mode='wb', fileobj=buffer) as f:
        for chunk in data_list:
            f.write(chunk)
    
    # Read back all data
    buffer.seek(0)
    with igzip.IGzipFile(mode='rb', fileobj=buffer) as f:
        decompressed = f.read()
    
    expected = b''.join(data_list)
    assert decompressed == expected


# Test 6: IGzipFile with different compression levels
@given(
    st.binary(min_size=0),
    st.integers(min_value=isal_zlib.ISAL_BEST_SPEED, 
                max_value=isal_zlib.ISAL_BEST_COMPRESSION)
)
@settings(max_examples=30)
def test_igzipfile_compression_levels(data, level):
    """Test IGzipFile with different compression levels."""
    buffer = io.BytesIO()
    
    with igzip.IGzipFile(mode='wb', fileobj=buffer, compresslevel=level) as f:
        f.write(data)
    
    buffer.seek(0)
    with igzip.IGzipFile(mode='rb', fileobj=buffer) as f:
        decompressed = f.read()
    
    assert decompressed == data


# Test 7: Empty data handling
@given(st.just(b''))
def test_empty_data_handling(data):
    """Test that empty data is handled correctly."""
    compressed = igzip.compress(data)
    decompressed = igzip.decompress(compressed)
    assert decompressed == data
    
    # Also test with IGzipFile
    buffer = io.BytesIO()
    with igzip.IGzipFile(mode='wb', fileobj=buffer) as f:
        f.write(data)
    
    buffer.seek(0)
    with igzip.IGzipFile(mode='rb', fileobj=buffer) as f:
        decompressed = f.read()
    
    assert decompressed == data


# Test 8: Large data handling
@given(st.binary(min_size=1000, max_size=5000))
@settings(max_examples=5, suppress_health_check=[HealthCheck.large_base_example, HealthCheck.data_too_large])
def test_large_data_handling(data):
    """Test compression/decompression of large data."""
    compressed = igzip.compress(data)
    decompressed = igzip.decompress(compressed)
    assert decompressed == data


# Test 9: Test open() function with BytesIO
@given(st.binary(min_size=0))
@settings(max_examples=20)
def test_open_function_with_bytesio(data):
    """Test the open() function with BytesIO objects."""
    buffer = io.BytesIO()
    
    # Write using open()
    with igzip.open(buffer, mode='wb') as f:
        f.write(data)
    
    # Read using open()
    buffer.seek(0)
    with igzip.open(buffer, mode='rb') as f:
        decompressed = f.read()
    
    assert decompressed == data


# Test 10: Test memoryview support in write()
@given(st.binary(min_size=0))
@settings(max_examples=20)
def test_memoryview_write_support(data):
    """Test that IGzipFile.write() accepts memoryview objects."""
    buffer = io.BytesIO()
    
    with igzip.IGzipFile(mode='wb', fileobj=buffer) as f:
        # Convert to memoryview and write
        mv = memoryview(data)
        written = f.write(mv)
        assert written == len(data)
    
    buffer.seek(0)
    with igzip.IGzipFile(mode='rb', fileobj=buffer) as f:
        decompressed = f.read()
    
    assert decompressed == data


# Test 11: Concatenated gzip members
@given(st.lists(st.binary(min_size=1), min_size=2, max_size=5))
@settings(max_examples=10)
def test_concatenated_gzip_members(data_list):
    """Test that decompress handles concatenated gzip members correctly."""
    # Create multiple compressed chunks
    compressed_chunks = [igzip.compress(data) for data in data_list]
    concatenated = b''.join(compressed_chunks)
    
    # decompress should handle concatenated gzip members
    decompressed = igzip.decompress(concatenated)
    expected = b''.join(data_list)
    assert decompressed == expected


if __name__ == "__main__":
    # Run all tests
    test_compress_decompress_round_trip()
    test_compression_levels_all_valid()
    test_compress_with_mtime()
    test_igzipfile_write_read_round_trip()
    test_igzipfile_multiple_writes()
    test_igzipfile_compression_levels()
    test_empty_data_handling()
    test_large_data_handling()
    test_open_function_with_bytesio()
    test_memoryview_write_support()
    test_concatenated_gzip_members()
    print("All tests completed!")