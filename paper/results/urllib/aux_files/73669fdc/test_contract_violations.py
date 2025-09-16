import urllib.response
import io
import tempfile
from hypothesis import given, strategies as st, assume
import inspect


@given(st.binary())
def test_addbase_breaks_temporaryfilewrapper_contract(data):
    """Test that addbase violates _TemporaryFileWrapper's contract."""
    fp = io.BytesIO(data)
    base = urllib.response.addbase(fp)
    
    # Check the signature mismatch
    parent_init = tempfile._TemporaryFileWrapper.__init__
    sig = inspect.signature(parent_init)
    
    # The parent expects delete_on_close parameter (added in Python 3.12+)
    params = list(sig.parameters.keys())
    
    # addbase passes delete=False but doesn't handle delete_on_close
    # This could cause issues in newer Python versions
    
    # Let's check what the parent class actually expects
    if 'delete_on_close' in params:
        # In Python 3.12+, the signature changed
        # But addbase still uses the old signature
        # This is a potential compatibility issue
        
        # Try to create directly with new signature
        try:
            # This should work with the new signature
            wrapper = tempfile._TemporaryFileWrapper(
                fp, '<test>', delete=False, delete_on_close=True
            )
            wrapper.close()
        except TypeError as e:
            # If it fails, there's a signature mismatch
            assert False, f"Signature mismatch: {e}"


@given(st.binary())
def test_addbase_delete_parameter_ignored(data):
    """Test that the delete=False parameter might not work as expected."""
    # Create a real temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf.write(data)
        tf.flush()
        temp_path = tf.name
    
    # Open it with addbase
    with open(temp_path, 'rb') as real_fp:
        base = urllib.response.addbase(real_fp)
        
        # The delete=False is hardcoded in addbase.__init__
        # Let's verify this doesn't interfere with normal file operations
        base.close()
    
    # File should still exist (delete=False)
    import os
    assert os.path.exists(temp_path)
    
    # Clean up
    os.unlink(temp_path)


@given(
    data=st.binary(),
    read_size=st.integers(min_value=-10, max_value=10)
)
def test_negative_read_size_handling(data, read_size):
    """Test how negative read sizes are handled."""
    fp = io.BytesIO(data)
    base = urllib.response.addbase(fp)
    
    if read_size < 0:
        # Negative size should read all remaining data
        result = base.read(read_size)
        expected = data
        assert result == expected
    else:
        result = base.read(read_size)
        expected = data[:read_size]
        assert result == expected


@given(st.binary(min_size=1))
def test_file_wrapper_passthrough_attributes(data):
    """Test that attributes are properly passed through the wrapper."""
    fp = io.BytesIO(data)
    base = urllib.response.addbase(fp)
    
    # These should be passed through to the underlying file
    if hasattr(fp, 'mode'):
        assert hasattr(base, 'mode')
    
    if hasattr(fp, 'name'):
        # But name is overridden!
        assert base.name == '<urllib response>'
        assert base.name != fp.name
    
    # Check other common file attributes
    for attr in ['read', 'readline', 'readlines', 'close']:
        assert hasattr(base, attr)


@given(
    hook_returns_value=st.one_of(
        st.none(),
        st.integers(),
        st.text(),
        st.booleans()
    )
)
def test_hook_return_value_ignored(hook_returns_value):
    """Test that hook return values are properly ignored."""
    fp = io.BytesIO(b"test")
    
    def hook_with_return():
        return hook_returns_value
    
    closehook = urllib.response.addclosehook(fp, hook_with_return)
    
    # The return value should be ignored, no error should occur
    closehook.close()
    assert closehook.closed


@given(
    data=st.binary(),
    code1=st.integers(),
    code2=st.integers()
)
def test_status_property_alias_consistency(data, code1, code2):
    """Test that status property stays consistent with getcode()."""
    fp = io.BytesIO(data)
    response = urllib.response.addinfourl(fp, {}, "test", code1)
    
    # status should equal code
    assert response.status == code1
    assert response.getcode() == code1
    
    # They should be the same thing (property alias)
    assert response.status == response.getcode()
    
    # Try to modify code attribute directly (shouldn't be possible normally)
    response.code = code2
    
    # Both should reflect the change
    assert response.status == code2
    assert response.getcode() == code2


@given(st.binary())
def test_context_manager_reentry_after_exception(data):
    """Test context manager behavior after exception in with block."""
    fp = io.BytesIO(data)
    base = urllib.response.addbase(fp)
    
    # First usage with exception
    try:
        with base:
            raise RuntimeError("Test error")
    except RuntimeError:
        pass
    
    # File should be closed after exception
    assert base.closed
    
    # Second entry should fail
    try:
        with base:
            pass
        assert False, "Should not allow reentry after exception"
    except ValueError as e:
        assert "closed file" in str(e).lower()


@given(
    num_args=st.integers(min_value=0, max_value=100)
)
def test_hookargs_memory_leak_potential(num_args):
    """Test that hookargs don't cause memory issues with many arguments."""
    fp = io.BytesIO(b"test")
    
    # Create many arguments
    args = tuple(f"arg_{i}" for i in range(num_args))
    
    def hook(*received_args):
        assert len(received_args) == num_args
    
    closehook = urllib.response.addclosehook(fp, hook, *args)
    
    # Check memory before close
    import sys
    if hasattr(closehook, 'hookargs'):
        assert len(closehook.hookargs) == num_args
    
    closehook.close()
    
    # After close, hookargs should be None (freed)
    assert closehook.hookargs is None


if __name__ == "__main__":
    import pytest
    
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))