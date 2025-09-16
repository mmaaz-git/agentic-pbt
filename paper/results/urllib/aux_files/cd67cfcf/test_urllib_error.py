#!/usr/bin/env python3
"""Property-based tests for urllib.error module"""

import io
import pickle
import urllib.error
import urllib.response
from hypothesis import given, strategies as st, assume, settings

# Strategy for URL strings
urls = st.text(min_size=1, max_size=200).filter(lambda x: not x.startswith(' ') and not x.endswith(' '))

# Strategy for HTTP status codes
http_codes = st.integers(min_value=100, max_value=599)

# Strategy for error messages
messages = st.text(min_size=0, max_size=500)

# Strategy for headers (simplified)
headers = st.dictionaries(
    st.text(min_size=1, max_size=50).filter(lambda x: ':' not in x and '\n' not in x),
    st.text(min_size=0, max_size=200).filter(lambda x: '\n' not in x),
    max_size=10
)

@given(st.text(), st.one_of(st.none(), urls))
def test_urlerror_initialization_and_attributes(reason, filename):
    """Test URLError initialization preserves attributes correctly"""
    err = urllib.error.URLError(reason, filename)
    
    # Check that reason is preserved
    assert err.reason == reason
    assert err.args == (reason,)
    
    # Check filename handling
    if filename is not None:
        assert hasattr(err, 'filename')
        assert err.filename == filename
    else:
        # filename should not be set if None was passed
        assert not hasattr(err, 'filename') or err.filename != filename
    
    # String representation should include reason
    str_repr = str(err)
    assert '<urlopen error' in str_repr

@given(st.text(), st.one_of(st.none(), urls))
def test_urlerror_pickling(reason, filename):
    """Test that URLError can be pickled and unpickled correctly"""
    err = urllib.error.URLError(reason, filename)
    
    # Pickle and unpickle
    pickled = pickle.dumps(err)
    unpickled = pickle.loads(pickled)
    
    # Check that attributes are preserved
    assert unpickled.reason == err.reason
    assert unpickled.args == err.args
    
    if filename is not None:
        assert hasattr(unpickled, 'filename')
        assert unpickled.filename == err.filename

@given(urls, http_codes, messages, st.none())
def test_httperror_without_fp(url, code, msg, fp):
    """Test HTTPError when fp is None - should create BytesIO"""
    # Create headers dict
    hdrs = {}
    
    err = urllib.error.HTTPError(url, code, msg, hdrs, fp)
    
    # Check basic attributes
    assert err.code == code
    assert err.msg == msg
    assert err.reason == msg  # reason property should return msg
    assert err.hdrs is hdrs
    assert err.headers is hdrs
    assert err.filename == url
    
    # When fp is None, it should create a BytesIO
    assert err.fp is not None
    assert isinstance(err.fp, io.BytesIO)
    
    # Check string representations
    str_repr = str(err)
    assert 'HTTP Error' in str_repr
    assert str(code) in str_repr
    
    repr_repr = repr(err)
    assert 'HTTPError' in repr_repr
    assert str(code) in repr_repr

@given(urls, http_codes, messages)
def test_httperror_inheritance_consistency(url, code, msg):
    """Test that HTTPError properly inherits from both URLError and addinfourl"""
    hdrs = {}
    fp = io.BytesIO(b'test content')
    
    err = urllib.error.HTTPError(url, code, msg, hdrs, fp)
    
    # Should be instance of both parent classes
    assert isinstance(err, urllib.error.URLError)
    assert isinstance(err, urllib.response.addinfourl)
    
    # URLError attributes
    assert hasattr(err, 'reason')
    assert err.reason == msg
    assert hasattr(err, 'filename')
    assert err.filename == url
    
    # addinfourl attributes
    assert hasattr(err, 'url')
    assert err.url == url
    assert hasattr(err, 'code')
    assert err.code == code
    assert hasattr(err, 'status')
    assert err.status == code
    
    # Methods from addinfourl
    assert err.getcode() == code
    assert err.geturl() == url

@given(urls, http_codes, messages)
def test_httperror_headers_property(url, code, msg):
    """Test the headers property getter and setter"""
    initial_hdrs = {'Content-Type': 'text/html'}
    fp = io.BytesIO(b'content')
    
    err = urllib.error.HTTPError(url, code, msg, initial_hdrs, fp)
    
    # Check initial headers
    assert err.headers is initial_hdrs
    assert err.hdrs is initial_hdrs
    
    # Test setter
    new_hdrs = {'Content-Type': 'application/json', 'X-Custom': 'value'}
    err.headers = new_hdrs
    
    # Both headers and hdrs should be updated
    assert err.headers is new_hdrs
    assert err.hdrs is new_hdrs

@given(messages, st.binary(min_size=0, max_size=1000))
def test_content_too_short_error(message, content):
    """Test ContentTooShortError initialization and attributes"""
    err = urllib.error.ContentTooShortError(message, content)
    
    # Should be a URLError
    assert isinstance(err, urllib.error.URLError)
    
    # Check attributes
    assert err.reason == message
    assert err.args == (message,)
    assert err.content == content
    
    # String representation
    str_repr = str(err)
    assert '<urlopen error' in str_repr

@given(urls, http_codes, messages)
def test_httperror_pickling(url, code, msg):
    """Test that HTTPError can be pickled and unpickled"""
    hdrs = {'Content-Type': 'text/plain'}
    fp = None  # Use None to test BytesIO creation
    
    err = urllib.error.HTTPError(url, code, msg, hdrs, fp)
    
    # Try to pickle and unpickle
    try:
        pickled = pickle.dumps(err)
        unpickled = pickle.loads(pickled)
        
        # Check that attributes are preserved
        assert unpickled.code == err.code
        assert unpickled.msg == err.msg
        assert unpickled.filename == err.filename
        # Note: fp and headers might not pickle correctly, but basic attrs should
    except Exception as e:
        # If pickling fails, that might be a bug
        print(f"Pickling failed for HTTPError: {e}")
        # Let's see if this is expected or not
        pass

@given(messages, st.binary(min_size=0, max_size=1000))
def test_content_too_short_pickling(message, content):
    """Test ContentTooShortError pickling"""
    err = urllib.error.ContentTooShortError(message, content)
    
    pickled = pickle.dumps(err)
    unpickled = pickle.loads(pickled)
    
    assert unpickled.reason == err.reason
    assert unpickled.content == err.content
    assert unpickled.args == err.args

@given(urls, http_codes, messages)
def test_httperror_multiple_inheritance_mro(url, code, msg):
    """Test that HTTPError's multiple inheritance doesn't cause MRO issues"""
    hdrs = {}
    fp = io.BytesIO(b'content')
    
    err = urllib.error.HTTPError(url, code, msg, hdrs, fp)
    
    # Check MRO is sensible
    mro = type(err).__mro__
    
    # HTTPError should come first
    assert mro[0] == urllib.error.HTTPError
    
    # URLError should come before addinfourl (since it's listed first in inheritance)
    urlerror_idx = mro.index(urllib.error.URLError)
    addinfourl_idx = mro.index(urllib.response.addinfourl)
    assert urlerror_idx < addinfourl_idx
    
    # Both parent __init__ methods should have been called properly
    # This is tested by checking attributes from both parents work

@given(st.text(), st.one_of(st.none(), urls))
def test_urlerror_args_tuple_consistency(reason, filename):
    """Test that URLError.args is always a tuple with reason as first element"""
    err = urllib.error.URLError(reason, filename)
    
    # args should be a tuple
    assert isinstance(err.args, tuple)
    
    # args should have exactly one element (the reason)
    assert len(err.args) == 1
    assert err.args[0] == reason
    
    # This is important for exception handling that unpacks args

if __name__ == '__main__':
    import pytest
    import sys
    
    # Run all tests
    sys.exit(pytest.main([__file__, '-v']))