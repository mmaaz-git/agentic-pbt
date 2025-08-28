import io
import tempfile
import os
from hypothesis import given, strategies as st, settings
import isal.igzip_threaded as igzip_threaded
import isal.igzip as igzip


@given(threads=st.integers(min_value=1, max_value=4))
@settings(max_examples=20)
def test_empty_data_handling(threads):
    """Test that empty data is handled correctly."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Write empty data
        with igzip_threaded.open(tmp_path, "wb", threads=threads) as f:
            f.write(b'')
        
        # Read it back
        with igzip_threaded.open(tmp_path, "rb") as f:
            recovered = f.read()
        
        assert recovered == b''
    finally:
        os.unlink(tmp_path)


@given(
    pattern=st.sampled_from([b'\x00', b'\xff', b'\x00\xff', b'\xde\xad\xbe\xef']),
    repeat_count=st.integers(min_value=1, max_value=10000),
    threads=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=30)
def test_repetitive_data(pattern, repeat_count, threads):
    """Test compression/decompression of highly repetitive data."""
    data = pattern * repeat_count
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        with igzip_threaded.open(tmp_path, "wb", threads=threads) as f:
            f.write(data)
        
        with igzip_threaded.open(tmp_path, "rb") as f:
            recovered = f.read()
        
        assert recovered == data
    finally:
        os.unlink(tmp_path)


@given(
    num_writes=st.integers(min_value=100, max_value=500),
    threads=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=10)
def test_many_small_writes(num_writes, threads):
    """Test many small writes to stress the queueing mechanism."""
    chunks = [b'x' * i for i in range(num_writes)]
    expected = b''.join(chunks)
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        with igzip_threaded.open(tmp_path, "wb", threads=threads, block_size=1024) as f:
            for chunk in chunks:
                f.write(chunk)
        
        with igzip_threaded.open(tmp_path, "rb") as f:
            recovered = f.read()
        
        assert recovered == expected
    finally:
        os.unlink(tmp_path)


@given(
    data=st.binary(min_size=1, max_size=10**4),
    threads=st.integers(min_value=2, max_value=4)
)
@settings(max_examples=20)
def test_concurrent_write_consistency(data, threads):
    """Test that using multiple threads produces valid output."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Write with multiple threads
        with igzip_threaded.open(tmp_path, "wb", threads=threads) as f:
            f.write(data)
        
        # Verify with standard igzip
        with igzip.open(tmp_path, "rb") as f:
            recovered = f.read()
        
        assert recovered == data
    finally:
        os.unlink(tmp_path)


@given(
    chunks=st.lists(st.binary(min_size=0, max_size=100), min_size=0, max_size=20),
    threads=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=30)
def test_write_after_flush(chunks, threads):
    """Test that writing after flush works correctly."""
    if not chunks:
        return  # Skip empty test
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        with igzip_threaded.open(tmp_path, "wb", threads=threads) as f:
            for i, chunk in enumerate(chunks):
                f.write(chunk)
                if i % 3 == 0:  # Flush every 3rd write
                    f.flush()
        
        # Should be able to read all data back
        with igzip_threaded.open(tmp_path, "rb") as f:
            recovered = f.read()
        
        assert recovered == b''.join(chunks)
    finally:
        os.unlink(tmp_path)


@given(
    block_size=st.integers(min_value=1, max_value=100)
)
@settings(max_examples=20)
def test_extremely_small_block_size(block_size):
    """Test with very small block sizes to stress the chunking logic."""
    data = b'Hello World! ' * 100
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        with igzip_threaded.open(tmp_path, "wb", threads=1, block_size=block_size) as f:
            f.write(data)
        
        with igzip_threaded.open(tmp_path, "rb") as f:
            recovered = f.read()
        
        assert recovered == data
    finally:
        os.unlink(tmp_path)


@given(data=st.binary(min_size=1, max_size=10**4))
@settings(max_examples=20)
def test_single_byte_writes(data):
    """Test writing data one byte at a time."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        with igzip_threaded.open(tmp_path, "wb", threads=1, block_size=1024) as f:
            for byte in data:
                f.write(bytes([byte]))
        
        with igzip_threaded.open(tmp_path, "rb") as f:
            recovered = f.read()
        
        assert recovered == data
    finally:
        os.unlink(tmp_path)