import urllib.response
import io
import os
import tempfile
from hypothesis import given, strategies as st, assume
import gc
import weakref


@given(st.binary(min_size=1))
def test_addbase_file_attribute_vs_fp_attribute(data):
    """Test the inconsistency between file and fp attributes."""
    original_fp = io.BytesIO(data)
    base = urllib.response.addbase(original_fp)
    
    # addbase sets both self.file (from parent) and self.fp
    assert hasattr(base, 'file')
    assert hasattr(base, 'fp')
    
    # They should be the same object
    assert base.file is base.fp
    assert base.file is original_fp
    
    # After close, both should still exist
    base.close()
    assert base.file is original_fp
    assert base.fp is original_fp
    
    # This dual attribute could cause confusion
    # The parent class uses 'file', but addbase adds 'fp' for compatibility


@given(st.binary())
def test_addclosehook_with_generator_function(data):
    """Test closehook with generator functions (which shouldn't be called as hooks)."""
    fp = io.BytesIO(data)
    
    def generator_hook():
        yield 1
        yield 2
    
    # This creates a closehook with a generator function
    closehook = urllib.response.addclosehook(fp, generator_hook)
    
    # When closed, it will call the generator function
    closehook.close()
    
    # The generator function returns a generator object, not None
    # This doesn't cause an error but might not be intended behavior
    assert closehook.closed


@given(
    data=st.binary(),
    hookargs=st.lists(
        st.one_of(
            st.binary(min_size=1000, max_size=10000),
            st.lists(st.integers(), min_size=100, max_size=1000)
        ),
        min_size=1,
        max_size=10
    )
)
def test_large_hookargs_memory(data, hookargs):
    """Test memory handling with large hook arguments."""
    fp = io.BytesIO(data)
    
    received_args = []
    def memory_hook(*args):
        received_args.extend(args)
    
    closehook = urllib.response.addclosehook(fp, memory_hook, *hookargs)
    
    # Before close, hookargs holds references
    assert closehook.hookargs == tuple(hookargs)
    
    closehook.close()
    
    # After close, hookargs is None (memory freed)
    assert closehook.hookargs is None
    assert closehook.closehook is None
    
    # But received_args still has the data
    assert len(received_args) == len(hookargs)


@given(st.binary())
def test_repr_with_none_file(data):
    """Test __repr__ when file attribute becomes None."""
    fp = io.BytesIO(data)
    base = urllib.response.addbase(fp)
    
    # Artificially set file to None (shouldn't happen normally)
    base.file = None
    
    # __repr__ should handle this gracefully
    try:
        repr_str = repr(base)
        # Should not crash
        assert 'addbase' in repr_str
    except:
        # If it crashes, that's a bug
        assert False, "__repr__ crashed with None file"


@given(
    data=st.binary(),
    buffer_size=st.integers(min_value=0, max_value=1000)
)
def test_readline_with_custom_size(data, buffer_size):
    """Test readline with size parameter."""
    assume(b'\n' in data)  # Need newlines for meaningful test
    
    fp = io.BytesIO(data)
    base = urllib.response.addbase(fp)
    
    # readline with size should work
    if buffer_size > 0:
        line = base.readline(buffer_size)
        assert len(line) <= buffer_size
    else:
        line = base.readline(buffer_size)
        # 0 or negative should read whole line
        if b'\n' in data:
            assert line.endswith(b'\n') or line == data


@given(st.binary(min_size=10))
def test_seek_tell_support(data):
    """Test seek and tell methods if available."""
    fp = io.BytesIO(data)
    base = urllib.response.addbase(fp)
    
    # BytesIO supports seek/tell
    if hasattr(base, 'seek') and hasattr(base, 'tell'):
        # Test basic seek/tell
        pos1 = base.tell()
        assert pos1 == 0
        
        base.read(5)
        pos2 = base.tell()
        assert pos2 == min(5, len(data))
        
        base.seek(0)
        pos3 = base.tell()
        assert pos3 == 0
        
        # Read should work after seek
        data_read = base.read(5)
        assert data_read == data[:5]


@given(
    data=st.binary(),
    close_file_before_wrapper=st.booleans()
)
def test_wrapper_with_already_closed_file(data, close_file_before_wrapper):
    """Test creating wrapper with an already closed file."""
    fp = io.BytesIO(data)
    
    if close_file_before_wrapper:
        fp.close()
    
    # Create wrapper with potentially closed file
    base = urllib.response.addbase(fp)
    
    if close_file_before_wrapper:
        # The wrapper is created but the file is already closed
        assert fp.closed
        
        # Operations should fail
        try:
            base.read()
            assert False, "Should not be able to read from closed file"
        except ValueError:
            pass
        
        # __enter__ should detect this
        try:
            with base:
                pass
            assert False, "Should not enter context with closed file"
        except ValueError as e:
            assert "closed file" in str(e).lower()


@given(st.binary())
def test_double_fp_close(data):
    """Test that closing fp directly affects wrapper."""
    fp = io.BytesIO(data)
    base = urllib.response.addbase(fp)
    
    # Close the underlying fp directly
    fp.close()
    
    # The wrapper doesn't know about this
    assert not base.closed  # Wrapper thinks it's open
    assert base.fp.closed   # But fp is closed
    
    # Operations should fail
    try:
        base.read()
        assert False, "Should fail to read"
    except ValueError:
        pass
    
    # Now close the wrapper too
    base.close()
    assert base.closed


if __name__ == "__main__":
    import pytest
    import sys
    
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))