#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import isal.isal_zlib as isal_zlib
import zlib
from hypothesis import given, strategies as st, settings, assume
import pytest


# Strategy for valid binary data
binary_data = st.binary(min_size=0, max_size=100000)
# Strategy for compression levels (isal supports 0-3)
isal_levels = st.integers(min_value=0, max_value=3)
# Strategy for wbits values (9-15 for zlib format, -9 to -15 for raw, 25-31 for gzip)
wbits_values = st.sampled_from([9, 10, 11, 12, 13, 14, 15, -9, -10, -11, -12, -13, -14, -15])


# Property 1: Round-trip compress/decompress
@given(data=binary_data, level=isal_levels)
def test_compress_decompress_round_trip(data, level):
    """Test that decompress(compress(data)) == data"""
    compressed = isal_zlib.compress(data, level=level)
    decompressed = isal_zlib.decompress(compressed)
    assert decompressed == data


# Property 2: Different compression levels produce decompressible data
@given(data=binary_data, level1=isal_levels, level2=isal_levels)
def test_different_compression_levels_decompress_same(data, level1, level2):
    """Test that data compressed at different levels decompresses to the same result"""
    compressed1 = isal_zlib.compress(data, level=level1)
    compressed2 = isal_zlib.compress(data, level=level2)
    decompressed1 = isal_zlib.decompress(compressed1)
    decompressed2 = isal_zlib.decompress(compressed2)
    assert decompressed1 == data
    assert decompressed2 == data
    assert decompressed1 == decompressed2


# Property 3: Compressor/Decompressor objects round-trip
@given(data=binary_data, level=isal_levels)
def test_compressor_decompressor_round_trip(data, level):
    """Test that compressor/decompressor objects work correctly"""
    compressor = isal_zlib.compressobj(level=level)
    compressed = compressor.compress(data) + compressor.flush()
    
    decompressor = isal_zlib.decompressobj()
    decompressed = decompressor.decompress(compressed)
    assert decompressed == data


# Property 4: Incremental compression/decompression
@given(chunks=st.lists(binary_data, min_size=1, max_size=10), level=isal_levels)
def test_incremental_compression_decompression(chunks, level):
    """Test that incremental compression/decompression works correctly"""
    # Compress incrementally
    compressor = isal_zlib.compressobj(level=level)
    compressed_parts = []
    for chunk in chunks:
        compressed_parts.append(compressor.compress(chunk))
    compressed_parts.append(compressor.flush())
    compressed = b''.join(compressed_parts)
    
    # Decompress all at once
    full_data = b''.join(chunks)
    decompressed = isal_zlib.decompress(compressed)
    assert decompressed == full_data
    
    # Also test incremental decompression
    decompressor = isal_zlib.decompressobj()
    decompressed_incremental = decompressor.decompress(compressed)
    assert decompressed_incremental == full_data


# Property 5: Cross-compatibility with standard zlib
@given(data=binary_data)
def test_cross_compatibility_with_standard_zlib(data):
    """Test that isal_zlib can decompress zlib-compressed data and vice versa"""
    # Standard zlib compress, isal decompress
    std_compressed = zlib.compress(data)
    isal_decompressed = isal_zlib.decompress(std_compressed)
    assert isal_decompressed == data
    
    # isal compress, standard zlib decompress
    isal_compressed = isal_zlib.compress(data)
    std_decompressed = zlib.decompress(isal_compressed)
    assert std_decompressed == data


# Property 6: adler32 checksum properties
@given(data=binary_data)
def test_adler32_deterministic(data):
    """Test that adler32 is deterministic"""
    checksum1 = isal_zlib.adler32(data)
    checksum2 = isal_zlib.adler32(data)
    assert checksum1 == checksum2
    
    # Also test compatibility with standard zlib
    std_checksum = zlib.adler32(data)
    assert checksum1 == std_checksum


# Property 7: crc32 checksum properties
@given(data=binary_data)
def test_crc32_deterministic(data):
    """Test that crc32 is deterministic"""
    checksum1 = isal_zlib.crc32(data)
    checksum2 = isal_zlib.crc32(data)
    assert checksum1 == checksum2
    
    # Also test compatibility with standard zlib
    std_checksum = zlib.crc32(data)
    assert checksum1 == std_checksum


# Property 8: crc32 incremental computation
@given(chunks=st.lists(binary_data, min_size=1, max_size=10))
def test_crc32_incremental(chunks):
    """Test that crc32 can be computed incrementally"""
    # Compute CRC32 all at once
    full_data = b''.join(chunks)
    full_crc = isal_zlib.crc32(full_data)
    
    # Compute CRC32 incrementally
    crc = 0
    for chunk in chunks:
        crc = isal_zlib.crc32(chunk, crc)
    
    assert crc == full_crc


# Property 9: adler32 incremental computation
@given(chunks=st.lists(binary_data, min_size=1, max_size=10))
def test_adler32_incremental(chunks):
    """Test that adler32 can be computed incrementally"""
    # Compute adler32 all at once
    full_data = b''.join(chunks)
    full_adler = isal_zlib.adler32(full_data)
    
    # Compute adler32 incrementally
    adler = 1  # adler32 starts with 1, not 0
    for chunk in chunks:
        adler = isal_zlib.adler32(chunk, adler)
    
    assert adler == full_adler


# Property 10: wbits parameter round-trip
@given(data=binary_data, wbits=wbits_values)
def test_wbits_round_trip(data, wbits):
    """Test that compress/decompress works with different wbits values"""
    compressed = isal_zlib.compress(data, wbits=wbits)
    decompressed = isal_zlib.decompress(compressed, wbits=wbits)
    assert decompressed == data


# Property 11: Empty data handling
def test_empty_data():
    """Test that empty data is handled correctly"""
    empty = b''
    compressed = isal_zlib.compress(empty)
    decompressed = isal_zlib.decompress(compressed)
    assert decompressed == empty
    
    # Test with compressor objects
    compressor = isal_zlib.compressobj()
    compressed_obj = compressor.compress(empty) + compressor.flush()
    decompressor = isal_zlib.decompressobj()
    decompressed_obj = decompressor.decompress(compressed_obj)
    assert decompressed_obj == empty


# Property 12: Decompress with max_length parameter
@given(data=binary_data, max_length=st.integers(min_value=1, max_value=1000))
def test_decompress_max_length(data, max_length):
    """Test that decompressor.decompress respects max_length parameter"""
    compressed = isal_zlib.compress(data)
    decompressor = isal_zlib.decompressobj()
    
    # Decompress with max_length
    partial = decompressor.decompress(compressed, max_length)
    assert len(partial) <= max_length
    
    # Get the rest
    remaining = decompressor.flush()
    full_decompressed = partial + remaining
    
    # Should equal original data
    assert full_decompressed == data


# Property 13: Large data handling
@given(size=st.integers(min_value=10000, max_value=100000))
def test_large_data_handling(size):
    """Test that large data is handled correctly"""
    # Create large but compressible data
    data = b'A' * size
    compressed = isal_zlib.compress(data)
    decompressed = isal_zlib.decompress(compressed)
    assert decompressed == data
    assert len(compressed) < len(data)  # Should achieve some compression


if __name__ == "__main__":
    # Run a quick sanity check
    print("Running quick sanity checks...")
    test_compress_decompress_round_trip()
    test_empty_data()
    print("Sanity checks passed! Run with pytest for full testing.")