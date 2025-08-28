import urllib.response
import io
import tempfile
import os
import threading
import weakref
from hypothesis import given, strategies as st, assume, settings, HealthCheck
import hypothesis


@given(
    data=st.binary(),
    operations=st.lists(
        st.sampled_from(['read', 'readline', 'readlines', 'seek', 'tell']),
        min_size=1,
        max_size=10
    )
)
def test_file_operations_through_wrapper(data, operations):
    """Test that file operations work correctly through the wrapper."""
    assume(len(data) > 0)
    fp = io.BytesIO(data)
    base = urllib.response.addbase(fp)
    
    for op in operations:
        if op == 'read':
            result = base.read(1)
            assert isinstance(result, bytes)
        elif op == 'readline':
            result = base.readline()
            assert isinstance(result, bytes)
        elif op == 'readlines':
            result = base.readlines()
            assert isinstance(result, list)
        elif op == 'seek':
            if hasattr(base, 'seek'):
                base.seek(0)
        elif op == 'tell':
            if hasattr(base, 'tell'):
                pos = base.tell()
                assert isinstance(pos, int)


@given(st.binary())
def test_nested_context_managers(data):
    """Test nested usage patterns of response objects."""
    fp1 = io.BytesIO(data)
    fp2 = io.BytesIO(data)
    
    base1 = urllib.response.addbase(fp1)
    base2 = urllib.response.addbase(fp2)
    
    with base1:
        with base2:
            assert not base1.closed
            assert not base2.closed
        assert base2.closed
        assert not base1.closed
    assert base1.closed


@given(
    data=st.binary(),
    num_hooks=st.integers(min_value=1, max_value=5)
)
def test_chained_closehooks(data, num_hooks):
    """Test chaining multiple close hooks."""
    call_order = []
    
    def make_hook(n):
        def hook():
            call_order.append(n)
        return hook
    
    fp = io.BytesIO(data)
    obj = fp
    
    # Chain multiple closehooks
    for i in range(num_hooks):
        obj = urllib.response.addclosehook(obj, make_hook(i))
    
    obj.close()
    
    # Only the outermost hook should be called
    assert len(call_order) == 1
    assert call_order[0] == num_hooks - 1


@given(st.binary(min_size=1))
def test_addbase_fileno_attribute(data):
    """Test that fileno attribute exists after wrapping."""
    fp = io.BytesIO(data)
    base = urllib.response.addbase(fp)
    
    # BytesIO doesn't have fileno, but the wrapper should handle this
    assert not hasattr(fp, 'fileno')
    # The wrapper doesn't add fileno if it doesn't exist
    assert not hasattr(base, 'fileno')


@given(
    data=st.binary(),
    headers=st.dictionaries(
        st.text(min_size=1, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))),
        st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')))
    )
)
def test_headers_mutation_after_creation(data, headers):
    """Test that mutating headers after creation affects the stored headers."""
    fp = io.BytesIO(data)
    info = urllib.response.addinfo(fp, headers)
    
    original_len = len(headers)
    returned_headers = info.info()
    
    # Mutate the original headers
    if headers:
        headers['new_key'] = 'new_value'
    
    # Check if mutation affects the stored headers
    assert len(info.info()) == original_len + (1 if headers else 0)
    assert info.info() is headers  # They should be the same object


@given(
    hook_exception=st.sampled_from([
        ValueError, RuntimeError, TypeError, KeyError, AttributeError
    ])
)
def test_different_hook_exceptions(hook_exception):
    """Test that different exception types in hooks are handled correctly."""
    fp = io.BytesIO(b"test")
    
    def failing_hook():
        raise hook_exception("Hook error")
    
    closehook = urllib.response.addclosehook(fp, failing_hook)
    
    try:
        closehook.close()
        assert False, f"Should have raised {hook_exception.__name__}"
    except hook_exception:
        pass
    
    # File should still be closed
    assert closehook.closed


@given(st.binary())
def test_weak_reference_support(data):
    """Test that response objects support weak references."""
    fp = io.BytesIO(data)
    base = urllib.response.addbase(fp)
    
    # Create weak reference
    weak_ref = weakref.ref(base)
    assert weak_ref() is base
    
    # Delete strong reference
    del base
    
    # Weak reference should be dead
    assert weak_ref() is None


@given(
    data=st.binary(),
    thread_count=st.integers(min_value=2, max_value=5)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_concurrent_close(data, thread_count):
    """Test that concurrent closes are handled safely."""
    fp = io.BytesIO(data)
    call_count = []
    
    def hook():
        call_count.append(1)
    
    closehook = urllib.response.addclosehook(fp, hook)
    
    def close_func():
        try:
            closehook.close()
        except:
            pass
    
    threads = [threading.Thread(target=close_func) for _ in range(thread_count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Hook should be called exactly once despite concurrent closes
    assert len(call_count) == 1
    assert closehook.closed


@given(
    data=st.binary(),
    headers=st.dictionaries(st.text(), st.text()),
    url=st.text(),
    code=st.integers()
)
def test_addinfourl_getstate_not_implemented(data, headers, url, code):
    """Test that getstate is not implemented (for pickling)."""
    fp = io.BytesIO(data)
    response = urllib.response.addinfourl(fp, headers, url, code)
    
    # Check if __getstate__ exists and works
    if hasattr(response, '__getstate__'):
        try:
            state = response.__getstate__()
        except:
            pass


@given(st.binary())
def test_addbase_exit_with_exception(data):
    """Test that __exit__ properly closes even with exception."""
    fp = io.BytesIO(data)
    base = urllib.response.addbase(fp)
    
    try:
        with base:
            raise ValueError("Test exception")
    except ValueError:
        pass
    
    assert base.closed


@given(
    data=st.binary(),
    headers=st.one_of(
        st.none(),
        st.dictionaries(st.text(), st.text()),
        st.just({}),
        st.lists(st.tuples(st.text(), st.text()))
    )
)
def test_various_header_types(data, headers):
    """Test that various header types are handled."""
    fp = io.BytesIO(data)
    
    # addinfo expects headers to be dict-like or have certain methods
    # Let's see what happens with different types
    try:
        info = urllib.response.addinfo(fp, headers)
        assert info.info() is headers
    except (TypeError, AttributeError):
        # Some header types might not be supported
        pass


@given(
    url=st.one_of(
        st.text(),
        st.just(""),
        st.just(None),
        st.integers(),
        st.just("http://example.com"),
        st.just("ftp://example.com"),
        st.just("file:///tmp/test")
    )
)
def test_various_url_types(url):
    """Test that various URL types are handled."""
    fp = io.BytesIO(b"test")
    headers = {}
    
    # addinfourl should accept any URL type
    response = urllib.response.addinfourl(fp, headers, url, 200)
    assert response.geturl() == url


@given(
    code=st.one_of(
        st.none(),
        st.integers(min_value=-1000, max_value=1000),
        st.just(200),
        st.just(404),
        st.just(500),
        st.text(),
        st.floats()
    )
)
def test_various_code_types(code):
    """Test that various code types are handled."""
    fp = io.BytesIO(b"test")
    headers = {}
    url = "http://test"
    
    # addinfourl should accept any code type
    response = urllib.response.addinfourl(fp, headers, url, code)
    assert response.getcode() == code
    assert response.status == code


if __name__ == "__main__":
    import pytest
    import sys
    
    # Run with pytest for better output
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))