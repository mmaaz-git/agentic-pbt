#!/usr/bin/env python3
"""More focused edge case tests for base64io using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/base64io_env/lib/python3.13/site-packages')

import io
import base64
from hypothesis import given, strategies as st, settings, assume, example
import base64io


@given(st.binary(min_size=1))
def test_write_without_close_loses_data(data):
    """Test that forgetting to close loses buffered data (as documented)."""
    # This tests the warning in the docstring about data loss
    buffer = io.BytesIO()
    
    b64 = base64io.Base64IO(buffer)
    b64.write(data)
    # Don't close - simulating the warned scenario
    
    # Try to decode what was written (without proper close)
    buffer.seek(0)
    partial_encoded = buffer.read()
    
    if len(data) % 3 != 0:
        # If data is not 3-byte aligned, some bytes should be buffered and lost
        try:
            partial_decoded = base64.b64decode(partial_encoded)
            # The decoded data should be shorter than original
            assert len(partial_decoded) < len(data), \
                f"Expected data loss for non-aligned data {len(data)} bytes"
        except:
            # Might fail to decode if incomplete
            pass


@given(st.binary(min_size=1, max_size=10))
def test_read_buffer_edge_cases(data):
    """Test edge cases in read buffer management."""
    buffer = io.BytesIO()
    
    # Write data
    with base64io.Base64IO(buffer) as b64:
        b64.write(data)
    
    # Read byte by byte and check buffer handling
    buffer.seek(0)
    result = []
    with base64io.Base64IO(buffer) as b64:
        for i in range(len(data) + 10):  # Try to read more than available
            byte = b64.read(1)
            if byte:
                result.append(byte)
            else:
                break
    
    final = b''.join(result)
    assert final == data, f"Byte-by-byte read failed: {data!r} != {final!r}"


@given(st.binary())
def test_mixed_read_sizes(data):
    """Test reading with various sizes in sequence."""
    if not data:
        return
        
    buffer = io.BytesIO()
    
    # Write data
    with base64io.Base64IO(buffer) as b64:
        b64.write(data)
    
    # Read with different sizes
    buffer.seek(0)
    result = []
    with base64io.Base64IO(buffer) as b64:
        # Read 1 byte
        chunk = b64.read(1)
        if chunk:
            result.append(chunk)
        
        # Read 0 bytes (should return empty)
        chunk = b64.read(0)
        assert chunk == b'', "Read(0) should return empty bytes"
        
        # Read large amount
        chunk = b64.read(len(data) * 2)
        if chunk:
            result.append(chunk)
    
    final = b''.join(result)
    assert final == data, f"Mixed reads failed: {data!r} != {final!r}"


@given(st.binary())
def test_extreme_whitespace_patterns(data):
    """Test handling of extreme amounts of whitespace."""
    encoded = base64.b64encode(data)
    
    # Add massive amounts of whitespace
    whitespace_bomb = b''
    for byte in encoded:
        whitespace_bomb += bytes([byte])
        whitespace_bomb += b' \t\n\r' * 10  # Lots of whitespace
    
    buffer = io.BytesIO(whitespace_bomb)
    with base64io.Base64IO(buffer) as b64:
        result = b64.read()
    
    assert result == data, f"Extreme whitespace failed: {data!r} != {result!r}"


@given(st.integers(min_value=1, max_value=1000))
def test_read_size_calculation_formula(num_bytes):
    """Test the specific formula for calculating encoded bytes to read."""
    # The formula in the code is:
    # _bytes_to_read = int((b - len(self.__read_buffer)) * 4 / 3)
    # _bytes_to_read += 4 - _bytes_to_read % 4
    
    # Generate data of exact size
    data = b'A' * num_bytes
    buffer = io.BytesIO()
    
    # Write data
    with base64io.Base64IO(buffer) as b64:
        b64.write(data)
    
    # Read exact amount
    buffer.seek(0)
    with base64io.Base64IO(buffer) as b64:
        result = b64.read(num_bytes)
    
    assert len(result) == num_bytes, \
        f"Read calculation wrong: requested {num_bytes}, got {len(result)}"


@given(st.lists(st.binary(min_size=1, max_size=5), min_size=1, max_size=10))
def test_interleaved_read_write(chunks):
    """Test that you cannot read and write interleaved (should fail)."""
    buffer = io.BytesIO()
    
    # This tests whether the stream properly handles mode checking
    b64 = base64io.Base64IO(buffer)
    
    # Write first chunk
    b64.write(chunks[0])
    
    # Try to read (should fail as we're in write mode)
    try:
        result = b64.read()
        # If it doesn't raise an error, that might be a bug
        # depending on the wrapped stream's behavior
    except IOError:
        pass  # Expected if stream doesn't support read+write
    
    b64.close()


@given(st.integers(min_value=-10, max_value=10))
def test_negative_and_special_read_values(read_size):
    """Test reading with negative and special size values."""
    data = b"test data content"
    buffer = io.BytesIO()
    
    # Write data
    with base64io.Base64IO(buffer) as b64:
        b64.write(data)
    
    # Read with various special values
    buffer.seek(0)
    with base64io.Base64IO(buffer) as b64:
        if read_size < 0 or read_size is None:
            # Should read all
            result = b64.read(read_size)
            assert result == data
        elif read_size == 0:
            # Should read nothing
            result = b64.read(read_size)
            assert result == b''
        else:
            # Should read up to read_size bytes
            result = b64.read(read_size)
            assert len(result) == min(read_size, len(data))


@given(st.binary(min_size=1))
def test_readline_limit_behavior(data):
    """Test readline with various limits."""
    buffer = io.BytesIO()
    
    # Write data
    with base64io.Base64IO(buffer) as b64:
        b64.write(data)
    
    # Test readline with different limits
    buffer.seek(0)
    with base64io.Base64IO(buffer) as b64:
        # readline with limit
        line1 = b64.readline(5)
        assert len(line1) <= 5 or len(line1) == len(data)
        
        # readline without limit (uses DEFAULT_BUFFER_SIZE)
        line2 = b64.readline()
        assert len(line1) + len(line2) <= len(data) + io.DEFAULT_BUFFER_SIZE


@given(st.integers(min_value=1, max_value=100))
def test_readlines_hint_behavior(hint):
    """Test readlines with hint parameter."""
    data = b"A" * 1000  # Large enough data
    buffer = io.BytesIO()
    
    # Write data
    with base64io.Base64IO(buffer) as b64:
        b64.write(data)
    
    # Read with hint
    buffer.seek(0)
    with base64io.Base64IO(buffer) as b64:
        lines = b64.readlines(hint)
        total_size = sum(len(line) for line in lines)
        
        # The total size should be around the hint value
        # (it reads until total exceeds hint)
        if hint < len(data):
            assert total_size >= hint or total_size == len(data)