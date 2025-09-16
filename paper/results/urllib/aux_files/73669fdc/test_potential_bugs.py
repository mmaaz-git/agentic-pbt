import urllib.response
import io
import gc
import sys
from hypothesis import given, strategies as st, assume


@given(st.binary())
def test_addbase_name_attribute_issue(data):
    """Test the hardcoded '<urllib response>' name in addbase."""
    fp = io.BytesIO(data)
    base = urllib.response.addbase(fp)
    
    # The name attribute is hardcoded as '<urllib response>'
    assert base.name == '<urllib response>'
    
    # This could be problematic if code expects the actual filename
    # For comparison, TemporaryFileWrapper normally gets the actual name
    import tempfile
    with tempfile.NamedTemporaryFile() as tf:
        tf.write(data)
        tf.flush()
        real_name = tf.name
        
        with open(real_name, 'rb') as real_fp:
            real_base = urllib.response.addbase(real_fp)
            # Even with a real file, the name is still hardcoded
            assert real_base.name == '<urllib response>'
            # The actual file name is lost
            assert real_base.name != real_name


@given(st.binary())
def test_delete_on_close_ignored(data):
    """Test that delete_on_close parameter is not passed to parent."""
    fp = io.BytesIO(data)
    
    # addbase.__init__ doesn't pass delete_on_close to parent
    # Let's check if this causes issues
    base = urllib.response.addbase(fp)
    
    # The parent class signature expects delete_on_close
    # but addbase doesn't provide it
    import inspect
    import tempfile
    
    parent_sig = inspect.signature(tempfile._TemporaryFileWrapper.__init__)
    params = list(parent_sig.parameters.keys())
    
    # Check that delete_on_close is expected but not provided
    assert 'delete_on_close' in params


@given(
    hook_calls_close=st.booleans(),
    data=st.binary()
)
def test_hook_calling_close_recursively(hook_calls_close, data):
    """Test what happens when a hook calls close() recursively."""
    fp = io.BytesIO(data)
    call_count = []
    
    def recursive_hook():
        call_count.append(1)
        if hook_calls_close and len(call_count) == 1:
            # First call - try to close again
            closehook.close()
    
    closehook = urllib.response.addclosehook(fp, recursive_hook)
    closehook.close()
    
    # The hook should only be called once due to None check
    assert len(call_count) == 1
    assert closehook.closehook is None


@given(st.binary())
def test_fp_attribute_after_close(data):
    """Test that fp attribute persists after close."""
    original_fp = io.BytesIO(data)
    base = urllib.response.addbase(original_fp)
    
    base.close()
    
    # fp attribute still exists and points to closed file
    assert base.fp is original_fp
    assert base.fp.closed
    
    # But operations on it will fail
    try:
        base.fp.read()
        assert False, "Should not be able to read from closed fp"
    except ValueError:
        pass


@given(
    data=st.binary(),
    headers=st.dictionaries(st.text(), st.text())
)
def test_info_headers_mutable_reference(data, headers):
    """Test that headers are stored by reference, not copy."""
    fp = io.BytesIO(data)
    info = urllib.response.addinfo(fp, headers)
    
    original_headers = info.info()
    
    # Modify the original headers dict
    if headers:
        headers['X-Modified'] = 'Yes'
    
    # The modification should be reflected in info()
    assert info.info() is headers
    if headers:
        assert 'X-Modified' in info.info()


@given(st.binary(min_size=1))
def test_repr_with_closed_file(data):
    """Test __repr__ on closed file."""
    fp = io.BytesIO(data)
    base = urllib.response.addbase(fp)
    
    repr_before = repr(base)
    base.close()
    repr_after = repr(base)
    
    # Both should work without crashing
    assert 'addbase' in repr_before
    assert 'addbase' in repr_after
    
    # The file attribute should still be accessible
    assert 'fp' in repr_after


@given(
    data=st.binary(),
    url=st.text(min_size=1000, max_size=10000)
)
def test_large_url_storage(data, url):
    """Test that very large URLs are stored without issues."""
    fp = io.BytesIO(data)
    response = urllib.response.addinfourl(fp, {}, url, 200)
    
    assert response.geturl() == url
    assert len(response.geturl()) == len(url)
    
    # Even after close
    response.close()
    assert response.geturl() == url


@given(st.binary())
def test_multiple_inheritance_mro(data):
    """Test method resolution order in inheritance chain."""
    fp = io.BytesIO(data)
    
    # Check MRO for each class
    import tempfile
    
    base = urllib.response.addbase(fp)
    assert tempfile._TemporaryFileWrapper in base.__class__.__mro__
    
    info = urllib.response.addinfo(io.BytesIO(data), {})
    assert urllib.response.addbase in info.__class__.__mro__
    
    url_resp = urllib.response.addinfourl(io.BytesIO(data), {}, "test", 200)
    assert urllib.response.addinfo in url_resp.__class__.__mro__
    assert urllib.response.addbase in url_resp.__class__.__mro__


@given(st.binary())
def test_gc_with_circular_reference(data):
    """Test garbage collection with circular references."""
    fp = io.BytesIO(data)
    
    class CircularHook:
        def __init__(self):
            self.closehook = None
        
        def __call__(self):
            pass
    
    hook = CircularHook()
    closehook = urllib.response.addclosehook(fp, hook)
    
    # Create circular reference
    hook.closehook = closehook
    
    # Delete our reference
    del closehook
    del hook
    
    # Force garbage collection
    gc.collect()
    
    # The file should eventually be closed by GC
    # (though we can't easily test this without weak references)


if __name__ == "__main__":
    import pytest
    
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))