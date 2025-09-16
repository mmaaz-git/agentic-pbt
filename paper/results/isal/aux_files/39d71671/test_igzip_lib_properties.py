#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import isal.igzip_lib as igzip_lib
from hypothesis import given, strategies as st, settings, assume
import pytest


@given(st.binary(min_size=0, max_size=100000))
@settings(max_examples=500)
def test_round_trip_deflate(data):
    compressed = igzip_lib.compress(data, flag=igzip_lib.COMP_DEFLATE)
    decompressed = igzip_lib.decompress(compressed, flag=igzip_lib.DECOMP_DEFLATE)
    assert decompressed == data


@given(st.binary(min_size=0, max_size=100000))
@settings(max_examples=500)
def test_round_trip_gzip(data):
    compressed = igzip_lib.compress(data, flag=igzip_lib.COMP_GZIP)
    decompressed = igzip_lib.decompress(compressed, flag=igzip_lib.DECOMP_GZIP)
    assert decompressed == data


@given(st.binary(min_size=0, max_size=100000))
@settings(max_examples=500)
def test_round_trip_zlib(data):
    compressed = igzip_lib.compress(data, flag=igzip_lib.COMP_ZLIB)
    decompressed = igzip_lib.decompress(compressed, flag=igzip_lib.DECOMP_ZLIB)
    assert decompressed == data


@given(st.binary(min_size=0, max_size=100000),
       st.sampled_from([igzip_lib.ISAL_BEST_SPEED, 
                        igzip_lib.ISAL_DEFAULT_COMPRESSION,
                        igzip_lib.ISAL_BEST_COMPRESSION]))
@settings(max_examples=500)
def test_all_compression_levels(data, level):
    compressed = igzip_lib.compress(data, level=level)
    decompressed = igzip_lib.decompress(compressed)
    assert decompressed == data


@given(st.binary(min_size=1, max_size=100000))
@settings(max_examples=500)
def test_compression_reduces_size_for_repetitive_data(data):
    repetitive_data = data * 10
    compressed = igzip_lib.compress(repetitive_data)
    # For repetitive data, compression should reduce size
    assert len(compressed) < len(repetitive_data)


@given(st.binary(min_size=0, max_size=100000))
@settings(max_examples=500)
def test_incremental_decompressor_matches_oneshot(data):
    compressed = igzip_lib.compress(data)
    
    # One-shot decompression
    oneshot_result = igzip_lib.decompress(compressed)
    
    # Incremental decompression
    decompressor = igzip_lib.IgzipDecompressor()
    incremental_result = decompressor.decompress(compressed)
    
    assert incremental_result == oneshot_result == data
    assert decompressor.eof


@given(st.binary(min_size=0, max_size=100000))
@settings(max_examples=500)
def test_incremental_decompressor_chunked(data):
    compressed = igzip_lib.compress(data)
    
    # Split compressed data into chunks
    chunk_size = max(1, len(compressed) // 3)
    chunks = [compressed[i:i+chunk_size] for i in range(0, len(compressed), chunk_size)]
    
    # Decompress incrementally
    decompressor = igzip_lib.IgzipDecompressor()
    result = b''
    for chunk in chunks:
        result += decompressor.decompress(chunk)
    
    assert result == data


@given(st.binary(min_size=0, max_size=10000),
       st.integers(min_value=1, max_value=15))
@settings(max_examples=200)
def test_hist_bits_parameter(data, hist_bits):
    compressed = igzip_lib.compress(data, hist_bits=hist_bits)
    decompressed = igzip_lib.decompress(compressed, hist_bits=hist_bits)
    assert decompressed == data


@given(st.binary(min_size=0, max_size=10000),
       st.sampled_from([igzip_lib.MEM_LEVEL_MIN,
                        igzip_lib.MEM_LEVEL_SMALL,
                        igzip_lib.MEM_LEVEL_MEDIUM,
                        igzip_lib.MEM_LEVEL_LARGE,
                        igzip_lib.MEM_LEVEL_EXTRA_LARGE,
                        igzip_lib.MEM_LEVEL_DEFAULT]))
@settings(max_examples=200)
def test_mem_level_parameter(data, mem_level):
    compressed = igzip_lib.compress(data, mem_level=mem_level)
    decompressed = igzip_lib.decompress(compressed)
    assert decompressed == data


@given(st.binary(min_size=0, max_size=100000))
@settings(max_examples=500)
def test_empty_unused_data_after_complete_decompression(data):
    compressed = igzip_lib.compress(data)
    decompressor = igzip_lib.IgzipDecompressor()
    result = decompressor.decompress(compressed)
    assert result == data
    assert decompressor.unused_data == b''


@given(st.binary(min_size=0, max_size=100000))
@settings(max_examples=200)
def test_decompressor_with_extra_data(data):
    compressed = igzip_lib.compress(data)
    extra_data = b'extra garbage data'
    combined = compressed + extra_data
    
    decompressor = igzip_lib.IgzipDecompressor()
    result = decompressor.decompress(combined)
    assert result == data
    # After decompression, unused_data should contain the extra data
    assert decompressor.unused_data == extra_data


@given(st.binary(min_size=0, max_size=10000))
@settings(max_examples=200)
def test_multiple_compress_same_result(data):
    # Compressing the same data multiple times should give the same result
    compressed1 = igzip_lib.compress(data)
    compressed2 = igzip_lib.compress(data)
    assert compressed1 == compressed2


@given(st.binary(min_size=0, max_size=10000))
@settings(max_examples=200)
def test_decompressor_max_length_parameter(data):
    compressed = igzip_lib.compress(data)
    
    decompressor = igzip_lib.IgzipDecompressor()
    
    # Decompress with max_length limit
    max_len = min(10, len(data))
    partial = decompressor.decompress(compressed, max_length=max_len)
    assert len(partial) <= max_len
    
    # Decompress the rest
    rest = decompressor.decompress(b'', max_length=-1)
    assert partial + rest == data


if __name__ == "__main__":
    print("Running property-based tests for isal.igzip_lib...")
    pytest.main([__file__, "-v", "--tb=short"])