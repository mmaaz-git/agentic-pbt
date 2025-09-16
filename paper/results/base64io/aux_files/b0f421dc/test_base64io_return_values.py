#!/usr/bin/env python3
"""Test return value semantics and other subtle behaviors."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/base64io_env/lib/python3.13/site-packages')

import io
import base64
from hypothesis import given, strategies as st, settings, note
import base64io


@given(st.binary(min_size=1))
def test_write_return_value_semantics(data):
    """Test that write() returns the number of bytes written from user perspective."""
    buffer = io.BytesIO()
    
    with base64io.Base64IO(buffer) as b64:
        bytes_written = b64.write(data)
        
        # The return value should be the number of user bytes written,
        # not the number of encoded bytes written to the underlying stream
        note(f"Data length: {len(data)}, bytes_written: {bytes_written}")
        
        # According to io.IOBase contract, write should return number of bytes written
        # from the caller's perspective
        assert bytes_written == len(data), \
            f"write() returned {bytes_written} but wrote {len(data)} user bytes"


@given(st.lists(st.binary(min_size=1, max_size=10), min_size=2, max_size=5))
def test_multiple_write_return_values(chunks):
    """Test write return values for multiple writes with buffering."""
    buffer = io.BytesIO()
    
    with base64io.Base64IO(buffer) as b64:
        total_written = 0
        for chunk in chunks:
            bytes_written = b64.write(chunk)
            note(f"Chunk length: {len(chunk)}, returned: {bytes_written}")
            
            # Each write should return the number of bytes from user perspective
            assert bytes_written == len(chunk), \
                f"write() returned {bytes_written} but chunk was {len(chunk)} bytes"
            total_written += bytes_written
        
        # Total should match all data written
        assert total_written == sum(len(c) for c in chunks)


@given(st.binary())
def test_readline_doesnt_respect_newlines(data_without_newlines):
    """Test that readline doesn't actually read lines."""
    # Add explicit newlines to data
    if not data_without_newlines:
        data_without_newlines = b"test"
    
    data = data_without_newlines[:len(data_without_newlines)//2] + b'\n' + \
           data_without_newlines[len(data_without_newlines)//2:]
    
    buffer = io.BytesIO()
    
    # Write data with newline
    with base64io.Base64IO(buffer) as b64:
        b64.write(data)
    
    # Read using readline
    buffer.seek(0)
    with base64io.Base64IO(buffer) as b64:
        line = b64.readline()
        
        # readline uses DEFAULT_BUFFER_SIZE, not actual line endings
        # So it should read more than just up to the newline
        note(f"Data: {data!r}, line read: {line!r}")
        
        # This is actually correct behavior according to the docstring -
        # it mentions that lines are read in chunks, not by line endings
        # But it's worth verifying this is intentional
        if len(data) > io.DEFAULT_BUFFER_SIZE:
            assert len(line) == io.DEFAULT_BUFFER_SIZE
        else:
            assert len(line) == len(data)


@given(st.binary(min_size=1))
def test_flush_method_behavior(data):
    """Test that flush() actually flushes the underlying stream."""
    
    class FlushTrackingIO(io.BytesIO):
        def __init__(self):
            super().__init__()
            self.flush_count = 0
        
        def flush(self):
            self.flush_count += 1
            return super().flush()
    
    buffer = FlushTrackingIO()
    
    with base64io.Base64IO(buffer) as b64:
        b64.write(data)
        initial_flushes = buffer.flush_count
        
        b64.flush()
        
        # flush() should have been called on wrapped stream
        assert buffer.flush_count > initial_flushes, \
            "flush() didn't call wrapped stream's flush()"


@given(st.binary())
def test_tell_seek_not_implemented(data):
    """Test that tell() and seek() raise appropriate errors."""
    buffer = io.BytesIO()
    
    with base64io.Base64IO(buffer) as b64:
        b64.write(data)
        
        # Base64IO inherits from io.IOBase which has default implementations
        # that raise UnsupportedOperation for seek/tell if not overridden
        try:
            position = b64.tell()
            # If this doesn't raise, it might be returning wrapped position
            # which would be wrong (encoded position != decoded position)
            note(f"tell() returned {position}")
        except (io.UnsupportedOperation, AttributeError):
            pass  # Expected
        
        try:
            b64.seek(0)
            # Seeking in a base64 stream is complex and likely not supported
        except (io.UnsupportedOperation, AttributeError):
            pass  # Expected


@given(st.binary(min_size=1))
def test_fileno_passthrough(data):
    """Test that fileno() is passed through correctly."""
    
    class FilenoMockIO(io.BytesIO):
        def fileno(self):
            return 42
    
    buffer = FilenoMockIO()
    
    with base64io.Base64IO(buffer) as b64:
        try:
            fd = b64.fileno()
            assert fd == 42, f"fileno() didn't pass through correctly: {fd}"
        except (io.UnsupportedOperation, AttributeError):
            # BytesIO doesn't normally have fileno
            pass


@given(st.binary())
def test_context_manager_exception_handling(data):
    """Test that context manager properly handles exceptions."""
    buffer = io.BytesIO()
    
    try:
        with base64io.Base64IO(buffer) as b64:
            b64.write(data)
            raise ValueError("Test exception")
    except ValueError:
        pass
    
    # The stream should still be closed after exception
    # Check that the buffer has the complete encoded data
    buffer.seek(0)
    encoded = buffer.read()
    if data:
        decoded = base64.b64decode(encoded)
        # Should have flushed on exit even with exception
        assert decoded == data, "Context manager didn't flush on exception"