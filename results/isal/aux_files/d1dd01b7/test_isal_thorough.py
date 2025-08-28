"""More thorough property-based tests for isal.igzip module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import io
from hypothesis import given, strategies as st, settings, HealthCheck
import isal.igzip as igzip
import isal.isal_zlib as isal_zlib


# Test with more examples and edge cases
@given(st.binary(min_size=0, max_size=10000))
@settings(max_examples=500)
def test_compress_decompress_extensive(data):
    """Extensive round-trip testing."""
    compressed = igzip.compress(data)
    decompressed = igzip.decompress(compressed)
    assert decompressed == data, f"Failed for data of length {len(data)}"


# Test special binary patterns
@given(st.one_of(
    st.binary(min_size=0, max_size=100),  # Random data
    st.binary(min_size=0, max_size=100).map(lambda x: b'\x00' * len(x)),  # All zeros
    st.binary(min_size=0, max_size=100).map(lambda x: b'\xff' * len(x)),  # All ones
    st.binary(min_size=0, max_size=100).map(lambda x: bytes([i % 256 for i in range(len(x))])),  # Sequential
    st.binary(min_size=0, max_size=100).map(lambda x: (b'pattern' * (len(x) // 7 + 1))[:len(x)]),  # Repeating
))
@settings(max_examples=200)
def test_special_patterns(data):
    """Test compression with special binary patterns."""
    compressed = igzip.compress(data)
    decompressed = igzip.decompress(compressed)
    assert decompressed == data


# Test edge case sizes
@given(st.sampled_from([0, 1, 2, 3, 4, 7, 8, 15, 16, 31, 32, 63, 64, 127, 128, 255, 256, 511, 512, 1023, 1024]))
def test_edge_case_sizes(size):
    """Test specific edge case sizes."""
    data = b'a' * size
    compressed = igzip.compress(data)
    decompressed = igzip.decompress(compressed)
    assert decompressed == data
    assert len(decompressed) == size


# Test invalid compression level handling
@given(
    st.binary(min_size=0, max_size=100),
    st.integers()
)
def test_invalid_compression_levels(data, level):
    """Test handling of invalid compression levels."""
    if not (isal_zlib.ISAL_BEST_SPEED <= level <= isal_zlib.ISAL_BEST_COMPRESSION):
        try:
            # compress function might use a default for invalid levels
            compressed = igzip.compress(data, compresslevel=level)
            # If it doesn't raise an error, the result should still be valid
            decompressed = igzip.decompress(compressed)
            assert decompressed == data
        except (ValueError, TypeError):
            # Expected behavior for invalid levels
            pass
    else:
        compressed = igzip.compress(data, compresslevel=level)
        decompressed = igzip.decompress(compressed)
        assert decompressed == data


# Test partial reads from IGzipFile
@given(
    st.binary(min_size=10, max_size=1000),
    st.integers(min_value=1, max_value=100)
)
@settings(max_examples=100)
def test_partial_reads(data, chunk_size):
    """Test reading in chunks from IGzipFile."""
    buffer = io.BytesIO()
    
    with igzip.IGzipFile(mode='wb', fileobj=buffer) as f:
        f.write(data)
    
    buffer.seek(0)
    chunks = []
    with igzip.IGzipFile(mode='rb', fileobj=buffer) as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            chunks.append(chunk)
    
    result = b''.join(chunks)
    assert result == data


# Test concurrent compression/decompression
@given(st.lists(st.binary(min_size=0, max_size=100), min_size=0, max_size=10))
def test_multiple_operations(data_list):
    """Test multiple compress/decompress operations."""
    results = []
    for data in data_list:
        compressed = igzip.compress(data)
        decompressed = igzip.decompress(compressed)
        results.append(decompressed == data)
    assert all(results)


if __name__ == "__main__":
    print("Running thorough tests...")
    test_compress_decompress_extensive()
    print("✓ Extensive round-trip test passed")
    test_special_patterns()
    print("✓ Special patterns test passed")
    test_edge_case_sizes()
    print("✓ Edge case sizes test passed")
    test_invalid_compression_levels()
    print("✓ Invalid compression levels test passed")
    test_partial_reads()
    print("✓ Partial reads test passed")
    test_multiple_operations()
    print("✓ Multiple operations test passed")
    print("\nAll thorough tests completed successfully!")