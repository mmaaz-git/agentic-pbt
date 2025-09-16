import urllib.response
import io
import tempfile
import os
from hypothesis import given, strategies as st, assume, settings
import hypothesis
import random
import string
from datetime import datetime


@given(data=st.binary())
def test_addbase_context_manager_closes_file(data):
    """Test that using addbase as context manager properly closes the file."""
    fp = io.BytesIO(data)
    base = urllib.response.addbase(fp)
    
    with base as b:
        assert not b.fp.closed
        assert not b.closed
    
    assert base.closed
    assert base.fp.closed


@given(data=st.binary())
def test_addbase_enter_on_closed_file(data):
    """Test that __enter__ on closed file raises ValueError."""
    fp = io.BytesIO(data)
    base = urllib.response.addbase(fp)
    base.close()
    
    try:
        with base:
            pass
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "closed file" in str(e).lower()


@given(
    data=st.binary(),
    hook_error=st.booleans()
)
def test_addclosehook_executes_hook_exactly_once(data, hook_error):
    """Test that close hook is executed exactly once even with multiple closes."""
    fp = io.BytesIO(data)
    call_count = []
    
    def hook(*args):
        call_count.append(1)
        if hook_error:
            raise ValueError("Hook error")
    
    hook_args = ("arg1", "arg2")
    closehook = urllib.response.addclosehook(fp, hook, *hook_args)
    
    # First close should execute the hook
    if hook_error:
        try:
            closehook.close()
        except ValueError:
            pass
    else:
        closehook.close()
    
    assert len(call_count) == 1
    
    # Second close should not execute the hook again
    closehook.close()
    assert len(call_count) == 1


@given(data=st.binary())
def test_addclosehook_none_hook(data):
    """Test that None hook doesn't cause issues."""
    fp = io.BytesIO(data)
    closehook = urllib.response.addclosehook(fp, None)
    closehook.close()
    assert closehook.closed


@given(
    data=st.binary(),
    headers=st.dictionaries(st.text(), st.text())
)
def test_addinfo_preserves_headers(data, headers):
    """Test that addinfo preserves and returns headers correctly."""
    fp = io.BytesIO(data)
    info = urllib.response.addinfo(fp, headers)
    
    assert info.info() is headers
    assert info.info() == headers
    
    # Headers should be accessible even after close
    info.close()
    assert info.info() == headers


@given(
    data=st.binary(),
    headers=st.dictionaries(st.text(), st.text()),
    url=st.text(),
    code=st.one_of(st.none(), st.integers())
)
def test_addinfourl_properties(data, headers, url, code):
    """Test that addinfourl correctly stores and returns all properties."""
    fp = io.BytesIO(data)
    response = urllib.response.addinfourl(fp, headers, url, code)
    
    assert response.geturl() == url
    assert response.getcode() == code
    assert response.status == code
    assert response.info() == headers
    
    # Properties should be accessible after close
    response.close()
    assert response.geturl() == url
    assert response.getcode() == code
    assert response.status == code
    assert response.info() == headers


@given(
    data=st.binary(),
    read_size=st.integers(min_value=0, max_value=1000)
)
def test_addbase_read_after_close(data, read_size):
    """Test that reading after close raises an error."""
    fp = io.BytesIO(data)
    base = urllib.response.addbase(fp)
    base.close()
    
    try:
        base.read(read_size)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


@given(data=st.binary())
def test_inheritance_chain_preserves_fp(data):
    """Test that fp reference is preserved through inheritance chain."""
    original_fp = io.BytesIO(data)
    
    base = urllib.response.addbase(original_fp)
    assert base.fp is original_fp
    
    info = urllib.response.addinfo(original_fp, {})
    assert info.fp is original_fp
    
    url_resp = urllib.response.addinfourl(original_fp, {}, "http://test", 200)
    assert url_resp.fp is original_fp


@given(
    data=st.binary(),
    headers=st.dictionaries(st.text(), st.text()),
    url=st.text()
)
def test_addinfourl_code_none_default(data, headers, url):
    """Test that code defaults to None when not provided."""
    fp = io.BytesIO(data)
    response = urllib.response.addinfourl(fp, headers, url)
    
    assert response.getcode() is None
    assert response.status is None


@given(data=st.binary(min_size=1))
def test_addbase_repr_doesnt_crash(data):
    """Test that __repr__ doesn't crash and contains expected info."""
    fp = io.BytesIO(data)
    base = urllib.response.addbase(fp)
    
    repr_str = repr(base)
    assert "addbase" in repr_str
    assert "fp" in repr_str


@given(
    data=st.binary(),
    hook_raises=st.booleans()
)
def test_addclosehook_ensures_file_closed_despite_hook_error(data, hook_raises):
    """Test that file is closed even if hook raises an exception."""
    fp = io.BytesIO(data)
    
    def failing_hook():
        if hook_raises:
            raise RuntimeError("Hook failed")
    
    closehook = urllib.response.addclosehook(fp, failing_hook)
    
    try:
        closehook.close()
    except RuntimeError:
        pass
    
    assert closehook.closed
    assert fp.closed


@given(st.binary())
def test_double_context_manager_usage(data):
    """Test that using context manager twice fails on second entry."""
    fp = io.BytesIO(data)
    base = urllib.response.addbase(fp)
    
    # First usage should work
    with base:
        pass
    
    # Second usage should fail
    try:
        with base:
            pass
        assert False, "Should have raised ValueError on second context entry"
    except ValueError as e:
        assert "closed file" in str(e).lower()


@given(
    hook_args=st.lists(st.text(), min_size=0, max_size=5)
)
def test_addclosehook_passes_correct_args(hook_args):
    """Test that hook receives the correct arguments."""
    fp = io.BytesIO(b"test")
    received_args = []
    
    def hook(*args):
        received_args.extend(args)
    
    closehook = urllib.response.addclosehook(fp, hook, *hook_args)
    closehook.close()
    
    assert received_args == list(hook_args)


@given(st.binary())
def test_tempfile_wrapper_delete_false(data):
    """Test that delete=False is properly passed to parent class."""
    # Create a real temp file to test delete behavior
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf.write(data)
        tf.flush()
        temp_path = tf.name
    
    # Open it with addbase
    with open(temp_path, 'rb') as fp:
        base = urllib.response.addbase(fp)
        base.close()
    
    # File should still exist since delete=False
    assert os.path.exists(temp_path)
    os.unlink(temp_path)


if __name__ == "__main__":
    import pytest
    import sys
    
    # Run with pytest for better output
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))