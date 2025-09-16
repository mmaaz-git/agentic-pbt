#!/usr/bin/env python3
"""Additional property tests for urllib.error"""

import urllib.error
import io
from hypothesis import given, strategies as st, assume

# Test property: HTTPError should behave as both an exception and a file-like object

@given(st.text(min_size=1), st.integers(100, 599), st.text(), st.binary())
def test_httperror_file_interface(url, code, msg, content):
    """Test that HTTPError acts as a file-like object"""
    fp = io.BytesIO(content)
    hdrs = {}
    
    err = urllib.error.HTTPError(url, code, msg, hdrs, fp)
    
    # Should be readable like a file
    data = err.read()
    assert data == content
    
    # After reading, should be at end
    more_data = err.read()
    assert more_data == b''
    
    # Should support seek
    err.seek(0)
    data_again = err.read()
    assert data_again == content

@given(st.text(min_size=1), st.integers(100, 599), st.text())
def test_httperror_inheritance_properties(url, code, msg):
    """Test that HTTPError properly inherits from both URLError and addinfourl"""
    err = urllib.error.HTTPError(url, code, msg, {}, None)
    
    # Property: err.reason should equal err.msg (from property definition)
    assert err.reason == err.msg
    
    # Property: err.status should equal err.code (from addinfourl)
    assert err.status == err.code
    
    # Property: getcode() should return code
    assert err.getcode() == err.code
    
    # Property: geturl() should return url  
    assert err.geturl() == url
    
    # Property: filename should equal url (set in __init__)
    assert err.filename == url

@given(st.text())
def test_urlerror_string_representation_invariant(reason):
    """Test URLError string representation always contains the pattern"""
    err = urllib.error.URLError(reason)
    str_repr = str(err)
    
    # Property: string representation always has this format
    assert str_repr.startswith('<urlopen error ')
    assert str_repr.endswith('>')
    
    # The reason should be in the string
    assert str(reason) in str_repr

@given(st.integers(100, 599), st.text())
def test_httperror_string_representation_invariant(code, msg):
    """Test HTTPError string representation format"""
    err = urllib.error.HTTPError('http://test.com', code, msg, {}, None)
    
    str_repr = str(err)
    repr_repr = repr(err)
    
    # Property: str() format
    assert str_repr.startswith('HTTP Error ')
    assert str(code) in str_repr
    assert msg in str_repr
    
    # Property: repr() format  
    assert repr_repr.startswith('<HTTPError ')
    assert str(code) in repr_repr
    assert repr_repr.endswith('>')

@given(st.text(), st.text())
def test_urlerror_args_consistency(reason, filename):
    """Test that URLError.args is always (reason,) regardless of filename"""
    err = urllib.error.URLError(reason, filename)
    
    # Property: args should always be a 1-tuple with just reason
    assert err.args == (reason,)
    
    # This should be true even when filename is provided
    err2 = urllib.error.URLError(reason)
    assert err2.args == (reason,)

if __name__ == '__main__':
    import pytest
    import sys
    sys.exit(pytest.main([__file__, '-v']))