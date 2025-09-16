import inspect
from unittest.mock import Mock, patch

import pytest
import requests.api
from hypothesis import given, strategies as st


@given(
    url=st.text(min_size=1),
    data=st.dictionaries(st.text(), st.text()),
    json_data=st.dictionaries(st.text(), st.text())
)
def test_put_json_parameter_contract(url, data, json_data):
    """Test that PUT function handles json parameter as documented in its docstring.
    
    The docstring claims: 'json: (optional) A JSON serializable Python object to send in the body of the :class:`Request`.'
    But the function signature is: put(url, data=None, **kwargs)
    """
    # Check if json parameter can be passed
    with patch('requests.api.request') as mock_request:
        mock_request.return_value = Mock()
        
        # This should work according to the docstring
        try:
            result = requests.api.put(url, data=data, json=json_data)
            # If it works, verify json was passed correctly
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            # json should be in kwargs
            assert 'json' in call_args.kwargs, "json parameter should be passed to request function"
            assert call_args.kwargs['json'] == json_data
        except TypeError as e:
            # If it fails due to unexpected keyword argument, that's the bug
            if "got an unexpected keyword argument 'json'" in str(e):
                pytest.fail(f"PUT function doesn't accept 'json' parameter despite documentation claiming it does: {e}")
            else:
                raise


@given(
    url=st.text(min_size=1),
    data=st.dictionaries(st.text(), st.text()),
    json_data=st.dictionaries(st.text(), st.text())
)
def test_patch_json_parameter_contract(url, data, json_data):
    """Test that PATCH function handles json parameter as documented in its docstring.
    
    The docstring claims: 'json: (optional) A JSON serializable Python object to send in the body of the :class:`Request`.'
    But the function signature is: patch(url, data=None, **kwargs)
    """
    # Check if json parameter can be passed
    with patch('requests.api.request') as mock_request:
        mock_request.return_value = Mock()
        
        # This should work according to the docstring
        try:
            result = requests.api.patch(url, data=data, json=json_data)
            # If it works, verify json was passed correctly
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            # json should be in kwargs
            assert 'json' in call_args.kwargs, "json parameter should be passed to request function"
            assert call_args.kwargs['json'] == json_data
        except TypeError as e:
            # If it fails due to unexpected keyword argument, that's the bug
            if "got an unexpected keyword argument 'json'" in str(e):
                pytest.fail(f"PATCH function doesn't accept 'json' parameter despite documentation claiming it does: {e}")
            else:
                raise


@given(
    url=st.text(min_size=1),
    allow_redirects=st.booleans()
)
def test_head_allow_redirects_default(url, allow_redirects):
    """Test that HEAD request sets allow_redirects=False by default as documented."""
    with patch('requests.api.request') as mock_request:
        mock_request.return_value = Mock()
        
        if allow_redirects:
            # Explicitly set allow_redirects
            requests.api.head(url, allow_redirects=allow_redirects)
            mock_request.assert_called_once_with("head", url, allow_redirects=allow_redirects)
        else:
            # Don't set allow_redirects, should default to False
            requests.api.head(url)
            mock_request.assert_called_once_with("head", url, allow_redirects=False)


@given(url=st.text(min_size=1))
def test_head_defaults_to_false_redirects(url):
    """Test that HEAD defaults allow_redirects to False when not specified."""
    with patch('requests.api.request') as mock_request:
        mock_request.return_value = Mock()
        
        requests.api.head(url)
        
        # Verify it was called with allow_redirects=False
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args.kwargs.get('allow_redirects') == False, \
            "HEAD should default allow_redirects to False"


@given(
    url=st.text(min_size=1),
    params=st.dictionaries(st.text(), st.text())
)
def test_get_method_name_consistency(url, params):
    """Test that get() passes 'get' as method name, not 'GET'."""
    with patch('requests.api.request') as mock_request:
        mock_request.return_value = Mock()
        
        requests.api.get(url, params=params)
        
        # First argument should be "get" (lowercase)
        mock_request.assert_called_once()
        method_arg = mock_request.call_args.args[0]
        assert method_arg == "get", f"get() should pass 'get' not '{method_arg}'"


@given(url=st.text(min_size=1))
def test_all_methods_lowercase_consistency(url):
    """Test that all HTTP method functions pass lowercase method names."""
    methods = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']
    
    with patch('requests.api.request') as mock_request:
        mock_request.return_value = Mock()
        
        for method_name in methods:
            mock_request.reset_mock()
            method_func = getattr(requests.api, method_name)
            
            # Call the method
            if method_name in ['post', 'put', 'patch']:
                method_func(url, data={})
            elif method_name == 'get':
                method_func(url, params={})
            else:
                method_func(url)
            
            # Check the method name passed to request
            mock_request.assert_called_once()
            passed_method = mock_request.call_args.args[0]
            assert passed_method == method_name, \
                f"{method_name}() should pass '{method_name}' not '{passed_method}'"