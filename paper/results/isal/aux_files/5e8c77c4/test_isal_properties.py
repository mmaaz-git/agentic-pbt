import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import io
import tempfile
from hypothesis import given, strategies as st, settings, assume
import isal.igzip as igzip
import isal.isal_zlib as isal_zlib


@given(st.binary())
@settings(max_examples=1000)
def test_compress_decompress_round_trip(data):
    """Test that decompress(compress(data)) == data"""
    compressed = igzip.compress(data)
    decompressed = igzip.decompress(compressed)
    assert decompressed == data


@given(st.binary(min_size=1), st.integers(min_value=0, max_value=3))
@settings(max_examples=500)
def test_compression_levels_produce_valid_gzip(data, level):
    """Test that all compression levels (0-3) produce valid gzip data"""
    compressed = igzip.compress(data, compresslevel=level)
    assert len(compressed) > 0
    decompressed = igzip.decompress(compressed)
    assert decompressed == data


@given(st.binary())
@settings(max_examples=500)
def test_igzipfile_write_read_round_trip(data):
    """Test that data written to IGzipFile can be read back correctly"""
    with tempfile.NamedTemporaryFile(suffix='.gz', delete=False) as tmp:
        tmp_name = tmp.name
    
    # Write data
    with igzip.IGzipFile(tmp_name, 'wb') as f:
        bytes_written = f.write(data)
        assert bytes_written == len(data)
    
    # Read data back
    with igzip.IGzipFile(tmp_name, 'rb') as f:
        read_data = f.read()
    
    assert read_data == data


@given(st.binary())
@settings(max_examples=500)
def test_empty_and_nonempty_data_handling(data):
    """Test that empty data is handled correctly"""
    compressed = igzip.compress(data)
    assert isinstance(compressed, bytes)
    if len(data) == 0:
        # Even empty data should produce a valid gzip header/trailer
        assert len(compressed) > 0
    decompressed = igzip.decompress(compressed)
    assert decompressed == data


@given(st.binary(min_size=1))
@settings(max_examples=500)
def test_compress_decompress_with_mtime(data):
    """Test compression with explicit mtime parameter"""
    import time
    mtime = int(time.time())
    compressed = igzip.compress(data, mtime=mtime)
    decompressed = igzip.decompress(compressed)
    assert decompressed == data


@given(st.lists(st.binary(min_size=1), min_size=2, max_size=5))
@settings(max_examples=200)
def test_concatenated_gzip_members(data_chunks):
    """Test that multiple gzip members can be concatenated and decompressed"""
    # Create multiple compressed chunks
    compressed_chunks = [igzip.compress(chunk) for chunk in data_chunks]
    concatenated = b''.join(compressed_chunks)
    
    # decompress should handle multiple members
    decompressed = igzip.decompress(concatenated)
    expected = b''.join(data_chunks)
    assert decompressed == expected


@given(st.binary())
@settings(max_examples=500)
def test_isal_zlib_compress_decompress_round_trip(data):
    """Test the lower-level isal_zlib interface"""
    compressed = isal_zlib.compress(data)
    decompressed = isal_zlib.decompress(compressed)
    assert decompressed == data


@given(st.binary(min_size=1))
@settings(max_examples=500)
def test_compression_reduces_or_maintains_size_for_random_data(data):
    """Test that compression doesn't dramatically increase size for random data"""
    compressed = igzip.compress(data)
    # Gzip header/trailer overhead is about 18 bytes
    # For random incompressible data, compressed size should be at most
    # original size + header/trailer + small deflate overhead
    # Allow up to 20% expansion for very small inputs
    max_expected_size = len(data) + 100 + int(len(data) * 0.2)
    assert len(compressed) <= max_expected_size


@given(st.binary())
@settings(max_examples=300)
def test_fileobj_interface_round_trip(data):
    """Test IGzipFile with BytesIO file objects"""
    buffer = io.BytesIO()
    
    # Write compressed data to buffer
    with igzip.IGzipFile(fileobj=buffer, mode='wb') as f:
        f.write(data)
    
    # Read compressed data from buffer
    buffer.seek(0)
    with igzip.IGzipFile(fileobj=buffer, mode='rb') as f:
        read_data = f.read()
    
    assert read_data == data