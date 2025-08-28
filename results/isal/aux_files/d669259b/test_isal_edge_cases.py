#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import isal.isal_zlib as isal_zlib
import zlib
from hypothesis import given, strategies as st, settings, assume, example
import pytest


# Test for potential integer overflow in CRC32 combining
@given(
    crc1=st.integers(min_value=0, max_value=2**32-1),
    crc2=st.integers(min_value=0, max_value=2**32-1),
    length2=st.integers(min_value=0, max_value=2**31-1)
)
@settings(max_examples=1000)
def test_crc32_combine_bounds(crc1, crc2, length2):
    """Test crc32_combine with various input values"""
    result = isal_zlib.crc32_combine(crc1, crc2, length2)
    # Result should be a valid 32-bit unsigned integer
    assert 0 <= result <= 2**32-1


# Test compression with various flush modes
@given(data=st.binary(min_size=1, max_size=10000))
@settings(max_examples=500)
def test_flush_modes(data):
    """Test different flush modes work correctly"""
    compressor = isal_zlib.compressobj()
    
    # Split data in half
    mid = len(data) // 2
    part1 = data[:mid]
    part2 = data[mid:]
    
    # Compress with different flush modes
    compressed = b''
    compressed += compressor.compress(part1)
    compressed += compressor.flush(isal_zlib.Z_SYNC_FLUSH)
    compressed += compressor.compress(part2)
    compressed += compressor.flush(isal_zlib.Z_FINISH)
    
    # Decompress and verify
    decompressed = isal_zlib.decompress(compressed)
    assert decompressed == data


# Test with gzip format (wbits 16-31)
@given(data=st.binary(min_size=0, max_size=10000))
@settings(max_examples=500)
def test_gzip_format(data):
    """Test compression with gzip format"""
    # wbits = 16 + (9 to 15) for gzip format
    for wbits in [25, 31]:  # Test min and max gzip wbits
        compressed = isal_zlib.compress(data, wbits=wbits)
        # For gzip format, need to use appropriate wbits for decompression
        decompressed = isal_zlib.decompress(compressed, wbits=wbits)
        assert decompressed == data


# Test raw deflate format (negative wbits)
@given(data=st.binary(min_size=0, max_size=10000))
@settings(max_examples=500)
def test_raw_deflate_format(data):
    """Test compression with raw deflate format"""
    # Negative wbits for raw deflate
    for wbits in [-15, -9]:  # Test min and max raw wbits
        compressed = isal_zlib.compress(data, wbits=wbits)
        decompressed = isal_zlib.decompress(compressed, wbits=wbits)
        assert decompressed == data


# Test compressor state after flush
@given(chunks=st.lists(st.binary(min_size=1, max_size=1000), min_size=2, max_size=5))
@settings(max_examples=500)
def test_compressor_state_after_flush(chunks):
    """Test that compressor can continue after various flush modes"""
    compressor = isal_zlib.compressobj()
    compressed_parts = []
    
    for i, chunk in enumerate(chunks[:-1]):
        compressed_parts.append(compressor.compress(chunk))
        # Use different flush modes
        if i % 2 == 0:
            compressed_parts.append(compressor.flush(isal_zlib.Z_SYNC_FLUSH))
        else:
            compressed_parts.append(compressor.flush(isal_zlib.Z_FULL_FLUSH))
    
    # Final chunk with Z_FINISH
    compressed_parts.append(compressor.compress(chunks[-1]))
    compressed_parts.append(compressor.flush(isal_zlib.Z_FINISH))
    
    compressed = b''.join(compressed_parts)
    decompressed = isal_zlib.decompress(compressed)
    assert decompressed == b''.join(chunks)


# Test decompressor with unconsumed tail
@given(data1=st.binary(min_size=1, max_size=1000), 
       data2=st.binary(min_size=1, max_size=1000))
@settings(max_examples=500)
def test_decompressor_unconsumed_tail(data1, data2):
    """Test decompressor handles multiple compressed blocks correctly"""
    compressed1 = isal_zlib.compress(data1)
    compressed2 = isal_zlib.compress(data2)
    combined = compressed1 + compressed2
    
    decompressor = isal_zlib.decompressobj()
    decompressed1 = decompressor.decompress(combined)
    
    # First decompress should give us data1
    assert decompressed1 == data1
    
    # There should be unconsumed tail
    if decompressor.unconsumed_tail:
        # Create new decompressor for the tail
        decompressor2 = isal_zlib.decompressobj()
        decompressed2 = decompressor2.decompress(decompressor.unconsumed_tail)
        assert decompressed2 == data2


# Test with predefined dictionary
@given(dictionary=st.binary(min_size=1, max_size=1000),
       data=st.binary(min_size=1, max_size=10000))
@settings(max_examples=500)
def test_compression_with_dictionary(dictionary, data):
    """Test compression with a predefined dictionary"""
    # Create compressor with dictionary
    compressor = isal_zlib.compressobj(zdict=dictionary)
    compressed = compressor.compress(data) + compressor.flush()
    
    # Create decompressor with same dictionary
    decompressor = isal_zlib.decompressobj(zdict=dictionary)
    decompressed = decompressor.decompress(compressed)
    
    assert decompressed == data


# Test extreme compression levels
@given(data=st.binary(min_size=0, max_size=10000))
@settings(max_examples=500)
def test_extreme_compression_levels(data):
    """Test boundary compression levels"""
    for level in [-1, 0, 3, 4]:  # -1 should be default, 4 should be clamped to 3
        try:
            compressed = isal_zlib.compress(data, level=level)
            decompressed = isal_zlib.decompress(compressed)
            assert decompressed == data
        except ValueError:
            # Level 4 might raise an error, which is fine
            pass


# Test checksums with extreme values
@given(data=st.binary(min_size=0, max_size=10000))
@settings(max_examples=500)
def test_checksum_extreme_initial_values(data):
    """Test checksums with extreme initial values"""
    # Test CRC32 with max initial value
    crc_max = isal_zlib.crc32(data, 0xFFFFFFFF)
    assert 0 <= crc_max <= 2**32-1
    
    # Test adler32 with max initial value
    adler_max = isal_zlib.adler32(data, 0xFFFFFFFF)
    assert 0 <= adler_max <= 2**32-1
    
    # Test with 0 initial values
    crc_zero = isal_zlib.crc32(data, 0)
    adler_zero = isal_zlib.adler32(data, 0)
    assert 0 <= crc_zero <= 2**32-1
    assert 0 <= adler_zero <= 2**32-1


# Test decompressor eof flag
@given(data=st.binary(min_size=1, max_size=1000))
@settings(max_examples=500)
def test_decompressor_eof_flag(data):
    """Test that decompressor correctly sets eof flag"""
    compressed = isal_zlib.compress(data)
    decompressor = isal_zlib.decompressobj()
    
    # Before decompression, eof should be False
    assert decompressor.eof == False
    
    # Decompress all data
    decompressed = decompressor.decompress(compressed)
    
    # After complete decompression, eof should be True
    assert decompressor.eof == True
    assert decompressed == data


# Test partial decompression
@given(data=st.binary(min_size=100, max_size=10000))
@settings(max_examples=500)
def test_partial_decompression(data):
    """Test partial decompression with max_length"""
    compressed = isal_zlib.compress(data)
    decompressor = isal_zlib.decompressobj()
    
    # Decompress in chunks of 10 bytes
    decompressed_parts = []
    remaining = compressed
    
    while remaining and not decompressor.eof:
        chunk = decompressor.decompress(remaining, 10)
        decompressed_parts.append(chunk)
        if decompressor.unconsumed_tail:
            remaining = decompressor.unconsumed_tail
        else:
            break
    
    # Get any remaining data
    final = decompressor.flush()
    if final:
        decompressed_parts.append(final)
    
    decompressed = b''.join(decompressed_parts)
    assert decompressed == data


if __name__ == "__main__":
    print("Running edge case tests...")
    pytest.main([__file__, "-v"])