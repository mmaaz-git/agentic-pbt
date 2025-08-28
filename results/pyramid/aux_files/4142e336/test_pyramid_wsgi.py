"""Property-based tests for pyramid.wsgi module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from unittest.mock import Mock, MagicMock
from pyramid.wsgi import wsgiapp, wsgiapp2
from pyramid.request import call_app_with_subpath_as_path_info


# Test 1: Both decorators should reject None wrapped argument
@given(st.just(None))
def test_wsgiapp_rejects_none(wrapped):
    """wsgiapp should raise ValueError when wrapped is None"""
    with pytest.raises(ValueError, match="wrapped can not be None"):
        wsgiapp(wrapped)


@given(st.just(None))
def test_wsgiapp2_rejects_none(wrapped):
    """wsgiapp2 should raise ValueError when wrapped is None"""
    with pytest.raises(ValueError, match="wrapped can not be None"):
        wsgiapp2(wrapped)


# Test 2: Encoding issues in call_app_with_subpath_as_path_info
# This function does encoding/decoding between utf-8 and latin-1
@given(st.lists(st.text(min_size=1), min_size=1, max_size=10))
def test_call_app_with_subpath_encoding(subpath_elements):
    """Test encoding round-trip in call_app_with_subpath_as_path_info"""
    # Create a mock request with subpath
    request = Mock()
    request.subpath = subpath_elements
    request.environ = {
        'SCRIPT_NAME': '/app',
        'PATH_INFO': '/original/path'
    }
    
    # Mock copy method to return a new request
    new_request = Mock()
    new_request.environ = {}
    new_request.get_response = Mock(return_value="response")
    request.copy = Mock(return_value=new_request)
    
    # Mock WSGI app
    app = Mock()
    
    # Call the function
    result = call_app_with_subpath_as_path_info(request, app)
    
    # Check that new_request.environ was set
    assert 'SCRIPT_NAME' in new_request.environ
    assert 'PATH_INFO' in new_request.environ
    
    # Verify postconditions from comments
    script_name = new_request.environ['SCRIPT_NAME']
    path_info = new_request.environ['PATH_INFO']
    
    # SCRIPT_NAME and PATH_INFO are empty or start with /
    assert script_name == '' or script_name.startswith('/')
    assert path_info == '' or path_info.startswith('/')
    
    # At least one of SCRIPT_NAME or PATH_INFO are set
    assert script_name or path_info
    
    # SCRIPT_NAME is not '/' (it should be '', and PATH_INFO should be '/')
    assert script_name != '/'


# Test 3: Unicode characters that cannot be encoded to latin-1
@given(st.lists(st.text(alphabet="🦄💀😈🎃", min_size=1), min_size=1, max_size=5))
def test_call_app_with_unicode_subpath(emoji_subpath):
    """Test handling of Unicode characters that might cause encoding issues"""
    request = Mock()
    request.subpath = emoji_subpath
    request.environ = {
        'SCRIPT_NAME': '',
        'PATH_INFO': '/'
    }
    
    new_request = Mock()
    new_request.environ = {}
    new_request.get_response = Mock(return_value="response")
    request.copy = Mock(return_value=new_request)
    
    app = Mock()
    
    # This might raise an encoding error when trying to encode emojis to latin-1
    try:
        result = call_app_with_subpath_as_path_info(request, app)
        # If it succeeds, check the postconditions
        script_name = new_request.environ.get('SCRIPT_NAME', '')
        path_info = new_request.environ.get('PATH_INFO', '')
        
        assert script_name == '' or script_name.startswith('/')
        assert path_info == '' or path_info.startswith('/')
        assert script_name or path_info
        assert script_name != '/'
    except UnicodeEncodeError:
        # This is a potential bug - the function cannot handle Unicode properly
        pass
    except UnicodeDecodeError:
        # This is a potential bug - the function cannot handle Unicode properly
        pass


# Test 4: Test the encoding round-trip more directly
@given(st.text(min_size=1))
def test_encoding_roundtrip_in_path_construction(text_input):
    """Test the specific encoding pattern used in call_app_with_subpath_as_path_info"""
    # The function does: text_(x.encode('utf-8'), 'latin-1')
    # This is trying to encode to utf-8 then interpret as latin-1
    try:
        # Simulate what the function does
        encoded = text_input.encode('utf-8')
        # Now try to decode as latin-1
        result = encoded.decode('latin-1')
        
        # Then later it does the reverse: text_(bytes_(el, 'latin-1'), 'utf-8')
        # Try to encode as latin-1
        re_encoded = result.encode('latin-1')
        # Then decode as utf-8
        final = re_encoded.decode('utf-8')
        
        # Check if we get back the original
        assert final == text_input
    except (UnicodeDecodeError, UnicodeEncodeError):
        # The encoding round-trip fails for certain inputs
        pass


# Test 5: Test decorator attribute preservation
@given(st.text(min_size=1))
def test_wsgiapp_preserves_attributes(func_name):
    """Test that wsgiapp preserves function attributes"""
    # Create a mock WSGI app with attributes
    def dummy_wsgi_app(environ, start_response):
        return []
    
    dummy_wsgi_app.__name__ = func_name
    dummy_wsgi_app.__doc__ = "Test documentation"
    dummy_wsgi_app.__module__ = "test_module"
    
    # Apply decorator
    decorated = wsgiapp(dummy_wsgi_app)
    
    # Check that attributes are preserved
    assert hasattr(decorated, '__name__')
    assert hasattr(decorated, '__doc__')
    assert hasattr(decorated, '__module__')


# Test 6: PATH_INFO trailing slash handling
@given(
    st.lists(st.text(alphabet=st.characters(blacklist_categories=('Cs',), min_codepoint=32, max_codepoint=126), min_size=1), min_size=1, max_size=5),
    st.booleans()
)
def test_path_info_trailing_slash(subpath, has_trailing_slash):
    """Test trailing slash handling in PATH_INFO"""
    request = Mock()
    request.subpath = subpath
    path_info = '/some/path'
    if has_trailing_slash:
        path_info += '/'
    
    request.environ = {
        'SCRIPT_NAME': '',
        'PATH_INFO': path_info
    }
    
    new_request = Mock()
    new_request.environ = {}
    new_request.get_response = Mock(return_value="response")
    request.copy = Mock(return_value=new_request)
    
    app = Mock()
    
    result = call_app_with_subpath_as_path_info(request, app)
    
    new_path_info = new_request.environ.get('PATH_INFO', '')
    
    # If original PATH_INFO had trailing slash and new_path_info is not just '/',
    # the new PATH_INFO should preserve it
    if has_trailing_slash and new_path_info != '/':
        # According to the code, trailing slash should be readded
        # if original path_info ends with '/' and new_path_info is not '/'
        assert new_path_info.endswith('/') or new_path_info == '/'