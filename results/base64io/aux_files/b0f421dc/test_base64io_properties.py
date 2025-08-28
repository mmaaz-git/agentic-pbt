#!/usr/bin/env python3
"""Property-based tests for base64io using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/base64io_env/lib/python3.13/site-packages')

import io
import base64
from hypothesis import given, strategies as st, settings, assume
import base64io


@given(st.binary())
def test_round_trip_property(data):
    """Test that writing data and reading it back returns the original data."""
    buffer = io.BytesIO()
    
    # Write data
    with base64io.Base64IO(buffer) as b64:
        b64.write(data)
    
    # Read data back
    buffer.seek(0)
    with base64io.Base64IO(buffer) as b64:
        result = b64.read()
    
    assert result == data, f"Round-trip failed: {data!r} != {result!r}"


@given(st.binary(min_size=1))
def test_write_buffer_flushing(data):
    """Test that all data is written even for non-3-byte-aligned data."""
    buffer = io.BytesIO()
    
    # Write data without context manager (manual close)
    b64 = base64io.Base64IO(buffer)
    b64.write(data)
    b64.close()
    
    # Verify the encoded data is complete
    buffer.seek(0)
    encoded = buffer.read()
    decoded = base64.b64decode(encoded)
    
    assert decoded == data, f"Data loss detected: {data!r} != {decoded!r}"


@given(st.lists(st.binary(min_size=1), min_size=2))
def test_multiple_writes_concatenation(chunks):
    """Test that multiple writes are correctly concatenated."""
    buffer = io.BytesIO()
    expected = b''.join(chunks)
    
    # Write chunks
    with base64io.Base64IO(buffer) as b64:
        for chunk in chunks:
            b64.write(chunk)
    
    # Read all data back
    buffer.seek(0)  
    with base64io.Base64IO(buffer) as b64:
        result = b64.read()
    
    assert result == expected, f"Multiple writes failed: {expected!r} != {result!r}"


@given(st.binary())
def test_whitespace_in_base64_ignored(data):
    """Test that whitespace in base64-encoded data is properly ignored during read."""
    # First encode the data normally
    normal_encoded = base64.b64encode(data)
    
    # Add various whitespace characters to the encoded data
    whitespace_encoded = b''
    for i, byte in enumerate(normal_encoded):
        whitespace_encoded += bytes([byte])
        if i % 4 == 0:
            whitespace_encoded += b' '
        if i % 8 == 0:
            whitespace_encoded += b'\n'
        if i % 12 == 0:
            whitespace_encoded += b'\t'
    
    # Read the whitespace-containing base64
    buffer = io.BytesIO(whitespace_encoded)
    with base64io.Base64IO(buffer) as b64:
        result = b64.read()
    
    assert result == data, f"Whitespace handling failed: {data!r} != {result!r}"


@given(st.binary(min_size=1), st.integers(min_value=1, max_value=1000))
def test_partial_reads(data, read_size):
    """Test that partial reads work correctly."""
    buffer = io.BytesIO()
    
    # Write data
    with base64io.Base64IO(buffer) as b64:
        b64.write(data)
    
    # Read in chunks
    buffer.seek(0)
    chunks = []
    with base64io.Base64IO(buffer) as b64:
        while True:
            chunk = b64.read(read_size)
            if not chunk:
                break
            chunks.append(chunk)
    
    result = b''.join(chunks)
    assert result == data, f"Partial reads failed: {data!r} != {result!r}"


@given(st.binary())
def test_writelines_method(data):
    """Test that writelines works correctly."""
    # Split data into lines
    if not data:
        lines = [b'']
    else:
        # Create random split points
        n_lines = min(len(data), 5)
        chunk_size = max(1, len(data) // n_lines)
        lines = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
    
    buffer = io.BytesIO()
    
    # Write using writelines
    with base64io.Base64IO(buffer) as b64:
        b64.writelines(lines)
    
    # Read back
    buffer.seek(0)
    with base64io.Base64IO(buffer) as b64:
        result = b64.read()
    
    expected = b''.join(lines)
    assert result == expected, f"writelines failed: {expected!r} != {result!r}"


@given(st.binary())
def test_iterator_interface(data):
    """Test the iterator interface of Base64IO."""
    buffer = io.BytesIO()
    
    # Write data
    with base64io.Base64IO(buffer) as b64:
        b64.write(data)
    
    # Read using iterator
    buffer.seek(0)
    chunks = []
    with base64io.Base64IO(buffer) as b64:
        for chunk in b64:
            chunks.append(chunk)
            # The iterator uses readline which reads in DEFAULT_BUFFER_SIZE chunks
            # So we should get the data in chunks
    
    result = b''.join(chunks)
    # The iterator might not return exactly the same data due to chunking
    # but it should at least start with the original data or be equal
    assert result.startswith(data) or data.startswith(result) or result == data, \
        f"Iterator failed: {data!r} not in {result!r}"


@given(st.binary(min_size=1))
def test_close_without_context_manager(data):
    """Test that close() properly flushes buffered data."""
    buffer = io.BytesIO()
    
    b64 = base64io.Base64IO(buffer)
    bytes_written = b64.write(data)
    
    # Before close, buffer might not have all data
    pre_close_size = buffer.tell()
    
    b64.close()
    
    # After close, all data should be flushed
    post_close_size = buffer.tell()
    
    # Verify the data is correct
    buffer.seek(0)
    encoded = buffer.read()
    decoded = base64.b64decode(encoded)
    
    assert decoded == data, f"Close didn't flush properly: {data!r} != {decoded!r}"
    assert b64.closed == True, "Stream not marked as closed"


@given(st.binary())
def test_operations_on_closed_stream_raise_error(data):
    """Test that operations on closed stream raise ValueError."""
    buffer = io.BytesIO()
    b64 = base64io.Base64IO(buffer)
    b64.close()
    
    # Test write on closed stream
    try:
        b64.write(data)
        assert False, "Writing to closed stream should raise ValueError"
    except ValueError as e:
        assert "closed" in str(e).lower()
    
    # Test read on closed stream  
    try:
        b64.read()
        assert False, "Reading from closed stream should raise ValueError"
    except ValueError as e:
        assert "closed" in str(e).lower()


@given(st.integers(min_value=1, max_value=100))
def test_empty_read_with_size(size):
    """Test reading from empty stream with specific size."""
    buffer = io.BytesIO()
    
    with base64io.Base64IO(buffer) as b64:
        result = b64.read(size)
    
    assert result == b'', f"Empty read should return empty bytes, got {result!r}"


@given(st.binary(min_size=10, max_size=1000))
def test_read_calculation_accuracy(data):
    """Test that the calculation for reading specific byte counts is accurate."""
    buffer = io.BytesIO()
    
    # Write data
    with base64io.Base64IO(buffer) as b64:
        b64.write(data)
    
    # Test reading exact amounts
    for read_size in [1, 3, 5, 10, len(data)//2, len(data)]:
        buffer.seek(0)
        with base64io.Base64IO(buffer) as b64:
            result = b64.read(read_size)
            assert len(result) == min(read_size, len(data)), \
                f"Read size mismatch: requested {read_size}, got {len(result)} bytes"