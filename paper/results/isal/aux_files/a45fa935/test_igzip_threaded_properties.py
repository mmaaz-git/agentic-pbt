import io
import tempfile
import os
from hypothesis import given, strategies as st, settings, assume, HealthCheck
import isal.igzip_threaded as igzip_threaded
import isal.igzip as igzip


@given(
    data=st.binary(min_size=0, max_size=10**6),
    threads=st.integers(min_value=1, max_value=4),
    block_size=st.integers(min_value=1024, max_value=64*1024)
)
@settings(max_examples=100)
def test_round_trip_property(data, threads, block_size):
    """Test that compressing and decompressing returns the original data."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Write compressed data using threaded writer
        with igzip_threaded.open(tmp_path, "wb", threads=threads, 
                                 block_size=block_size) as f:
            f.write(data)
        
        # Read it back using threaded reader
        with igzip_threaded.open(tmp_path, "rb") as f:
            recovered = f.read()
        
        assert recovered == data, f"Data mismatch: original length {len(data)}, recovered length {len(recovered)}"
    finally:
        os.unlink(tmp_path)


@given(
    data=st.binary(min_size=1, max_size=10**5),
    block_size=st.integers(min_value=1024, max_value=64*1024)
)
@settings(max_examples=50)
def test_consistency_with_non_threaded(data, block_size):
    """Test that threaded (threads=1) and non-threaded (threads=0) produce compatible output."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp1:
        tmp1_path = tmp1.name
    with tempfile.NamedTemporaryFile(delete=False) as tmp2:
        tmp2_path = tmp2.name
    
    try:
        # Write with threads=0 (uses igzip.open)
        with igzip_threaded.open(tmp1_path, "wb", threads=0) as f:
            f.write(data)
        
        # Write with threads=1 (uses threaded implementation)
        with igzip_threaded.open(tmp2_path, "wb", threads=1, 
                                 block_size=block_size) as f:
            f.write(data)
        
        # Both files should decompress to the same data
        with igzip.open(tmp1_path, "rb") as f:
            data1 = f.read()
        with igzip.open(tmp2_path, "rb") as f:
            data2 = f.read()
        
        assert data1 == data2 == data
    finally:
        os.unlink(tmp1_path)
        os.unlink(tmp2_path)


@given(
    block_size=st.integers(min_value=1024, max_value=4096),
    threads=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=20)
def test_large_block_handling(block_size, threads):
    """Test that blocks larger than block_size are handled correctly."""
    # Create data that's 3x the block_size to ensure we test the splitting logic
    data = b'A' * (block_size * 3)
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Write data that's larger than block_size
        with igzip_threaded.open(tmp_path, "wb", threads=threads,
                                 block_size=block_size) as f:
            bytes_written = f.write(data)
            assert bytes_written == len(data)
        
        # Read it back
        with igzip_threaded.open(tmp_path, "rb") as f:
            recovered = f.read()
        
        assert recovered == data
    finally:
        os.unlink(tmp_path)


@given(
    chunks=st.lists(st.binary(min_size=1, max_size=10**4), 
                    min_size=2, max_size=10),
    threads=st.integers(min_value=1, max_value=3),
    block_size=st.integers(min_value=1024, max_value=16*1024)
)
@settings(max_examples=30)
def test_multiple_writes_consistency(chunks, threads, block_size):
    """Test that writing in multiple chunks produces the same result as writing all at once."""
    full_data = b''.join(chunks)
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp1:
        tmp1_path = tmp1.name
    with tempfile.NamedTemporaryFile(delete=False) as tmp2:
        tmp2_path = tmp2.name
    
    try:
        # Write in chunks
        with igzip_threaded.open(tmp1_path, "wb", threads=threads,
                                 block_size=block_size) as f:
            for chunk in chunks:
                f.write(chunk)
        
        # Write all at once
        with igzip_threaded.open(tmp2_path, "wb", threads=threads,
                                 block_size=block_size) as f:
            f.write(full_data)
        
        # Both should decompress to the same data
        with igzip.open(tmp1_path, "rb") as f:
            data1 = f.read()
        with igzip.open(tmp2_path, "rb") as f:
            data2 = f.read()
        
        assert data1 == data2 == full_data
    finally:
        os.unlink(tmp1_path)
        os.unlink(tmp2_path)


@given(
    data=st.binary(min_size=0, max_size=10**5),
    threads=st.integers(min_value=-2, max_value=4),
    block_size=st.integers(min_value=1024, max_value=64*1024)
)
@settings(max_examples=30)
def test_thread_parameter_handling(data, threads, block_size):
    """Test that different thread values work correctly."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Write with specified thread count
        with igzip_threaded.open(tmp_path, "wb", threads=threads,
                                 block_size=block_size) as f:
            f.write(data)
        
        # Read it back
        with igzip_threaded.open(tmp_path, "rb") as f:
            recovered = f.read()
        
        assert recovered == data
    finally:
        os.unlink(tmp_path)


@given(
    data=st.binary(min_size=1, max_size=10**5),
    threads=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=30)
def test_flush_creates_new_gzip_stream(data, threads):
    """Test that flush() ends the current gzip stream and starts a new one."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Write data with a flush in between
        with igzip_threaded.open(tmp_path, "wb", threads=threads) as f:
            f.write(data[:len(data)//2])
            f.flush()  # This should end the stream and start a new one
            f.write(data[len(data)//2:])
        
        # Should be able to read it back
        with igzip_threaded.open(tmp_path, "rb") as f:
            recovered = f.read()
        
        # The data should be recoverable (two concatenated gzip streams)
        assert recovered == data
    finally:
        os.unlink(tmp_path)


@given(data=st.binary(min_size=0, max_size=10**4))
@settings(max_examples=30)
def test_bytes_vs_memoryview_write(data):
    """Test that writing bytes vs memoryview produces the same result."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp1:
        tmp1_path = tmp1.name
    with tempfile.NamedTemporaryFile(delete=False) as tmp2:
        tmp2_path = tmp2.name
    
    try:
        # Write as bytes
        with igzip_threaded.open(tmp1_path, "wb", threads=1) as f:
            f.write(data)
        
        # Write as memoryview
        with igzip_threaded.open(tmp2_path, "wb", threads=1) as f:
            if data:
                f.write(memoryview(data))
            else:
                f.write(data)
        
        # Both should decompress to the same data
        with igzip.open(tmp1_path, "rb") as f:
            data1 = f.read()
        with igzip.open(tmp2_path, "rb") as f:
            data2 = f.read()
        
        assert data1 == data2 == data
    finally:
        os.unlink(tmp1_path)
        os.unlink(tmp2_path)