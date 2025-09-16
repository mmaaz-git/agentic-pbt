import os
import gc
import atexit
import tempfile
import shutil
from unittest import mock
from hypothesis import given, strategies as st, assume, settings
import requests.certs


@given(st.integers(min_value=1, max_value=10))
def test_where_gc_behavior(iterations):
    """Test behavior under garbage collection pressure."""
    import importlib
    
    for _ in range(iterations):
        # Force module reload to reset global state
        try:
            importlib.reload(requests.certs)
        except:
            # If reload fails, continue with existing module
            pass
        
        path = requests.certs.where()
        assert os.path.exists(path)
        
        # Force garbage collection
        gc.collect()
        
        # Path should still be valid after GC
        assert os.path.exists(path)
        assert requests.certs.where() == path


def test_where_atexit_handler():
    """Test that atexit handler is properly registered."""
    import importlib
    
    # Reload to ensure fresh state
    try:
        importlib.reload(requests.certs)
    except:
        pass
    
    # Call where() to trigger initialization
    path = requests.certs.where()
    
    # Check if exit handler was registered
    # This is implementation-specific but tests for proper cleanup registration
    if hasattr(requests.certs, 'exit_cacert_ctx'):
        # The function should be registered with atexit
        # We can't easily check atexit's internal registry, but we can
        # verify the function exists and is callable
        assert callable(requests.certs.exit_cacert_ctx)


@given(st.data())
def test_where_with_mock_failures(data):
    """Test behavior when underlying operations fail."""
    import importlib
    
    # Test various failure modes
    failure_mode = data.draw(st.sampled_from([
        'file_not_found',
        'permission_error',
        'os_error'
    ]))
    
    # Reload module to reset state
    try:
        importlib.reload(requests.certs) 
    except:
        return  # Skip if reload fails
    
    if failure_mode == 'file_not_found':
        # Mock files() to return non-existent path
        with mock.patch('requests.certs.files') as mock_files:
            mock_joinpath = mock.MagicMock()
            mock_files.return_value.joinpath.return_value = mock_joinpath
            
            # as_file should handle the path
            with mock.patch('requests.certs.as_file') as mock_as_file:
                mock_ctx = mock.MagicMock()
                mock_ctx.__enter__.return_value = '/nonexistent/path/cert.pem'
                mock_as_file.return_value = mock_ctx
                
                # Reset global state
                if hasattr(requests.certs, '_CACERT_PATH'):
                    requests.certs._CACERT_PATH = None
                if hasattr(requests.certs, '_CACERT_CTX'):
                    requests.certs._CACERT_CTX = None
                
                # This should return a path even if it doesn't exist
                # The function doesn't validate the path exists
                result = requests.certs.where()
                assert isinstance(result, str)
    
    elif failure_mode == 'permission_error':
        # Test with a path that exists but might not be readable
        with mock.patch('requests.certs.as_file') as mock_as_file:
            mock_ctx = mock.MagicMock()
            mock_ctx.__enter__.return_value = '/etc/shadow'  # Usually not readable
            mock_as_file.return_value = mock_ctx
            
            # Reset global state
            if hasattr(requests.certs, '_CACERT_PATH'):
                requests.certs._CACERT_PATH = None
            if hasattr(requests.certs, '_CACERT_CTX'):
                requests.certs._CACERT_CTX = None
            
            # The function should still return the path
            result = requests.certs.where()
            assert isinstance(result, str)


def test_where_path_type():
    """Test that where() always returns a string path."""
    path = requests.certs.where()
    assert isinstance(path, str)
    assert not isinstance(path, bytes)
    # Path should be absolute
    assert os.path.isabs(path)


def test_where_unicode_path_handling():
    """Test handling of paths with unicode characters."""
    import importlib
    
    # Create a temporary directory with unicode characters
    with tempfile.TemporaryDirectory(prefix='测试_café_') as tmpdir:
        # Mock the path to return a unicode path
        unicode_path = os.path.join(tmpdir, 'ÿöü_cert.pem')
        
        # Create a dummy cert file
        with open(unicode_path, 'w') as f:
            f.write('-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----\n')
        
        with mock.patch('requests.certs.as_file') as mock_as_file:
            mock_ctx = mock.MagicMock()
            mock_ctx.__enter__.return_value = unicode_path
            mock_as_file.return_value = mock_ctx
            
            # Reload and reset
            try:
                importlib.reload(requests.certs)
            except:
                pass
            
            if hasattr(requests.certs, '_CACERT_PATH'):
                requests.certs._CACERT_PATH = None
            if hasattr(requests.certs, '_CACERT_CTX'):
                requests.certs._CACERT_CTX = None
            
            # Should handle unicode paths correctly
            result = requests.certs.where()
            assert isinstance(result, str)
            assert result == unicode_path


@given(st.integers(min_value=1, max_value=5))
def test_where_after_module_manipulation(num_calls):
    """Test behavior when module attributes are manipulated."""
    
    # Save original state
    original_cacert_path = getattr(requests.certs, '_CACERT_PATH', None)
    original_cacert_ctx = getattr(requests.certs, '_CACERT_CTX', None)
    
    try:
        # Get initial path
        path1 = requests.certs.where()
        
        # Try various manipulations
        for i in range(num_calls):
            # Delete attributes if they exist
            if hasattr(requests.certs, '_CACERT_PATH'):
                delattr(requests.certs, '_CACERT_PATH')
            if hasattr(requests.certs, '_CACERT_CTX'):
                delattr(requests.certs, '_CACERT_CTX')
            
            # Should handle missing attributes gracefully
            path2 = requests.certs.where()
            assert isinstance(path2, str)
            
            # Set attributes to wrong types
            requests.certs._CACERT_PATH = i  # Wrong type
            requests.certs._CACERT_CTX = None
            
            # Should reinitialize when path is wrong type
            path3 = requests.certs.where()
            assert isinstance(path3, str)
    
    finally:
        # Restore original state
        if original_cacert_path is not None:
            requests.certs._CACERT_PATH = original_cacert_path
        if original_cacert_ctx is not None:
            requests.certs._CACERT_CTX = original_cacert_ctx


def test_where_return_value_properties():
    """Test properties of the returned path value."""
    path = requests.certs.where()
    
    # Should not be empty
    assert len(path) > 0
    
    # Should not contain null bytes
    assert '\x00' not in path
    
    # Should be a normalized path
    assert path == os.path.normpath(path)
    
    # Should not have trailing slashes (it's a file, not directory)
    assert not path.endswith(os.sep)
    
    # Should have .pem extension (based on implementation)
    assert path.endswith('.pem') or path.endswith('.crt')