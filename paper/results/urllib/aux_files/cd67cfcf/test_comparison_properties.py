#!/usr/bin/env python3
"""Test comparison and equality properties"""

import urllib.error
from hypothesis import given, strategies as st

@given(st.text(), st.text())
def test_urlerror_equality(reason1, reason2):
    """Test URLError equality behavior"""
    err1 = urllib.error.URLError(reason1)
    err2 = urllib.error.URLError(reason1)
    err3 = urllib.error.URLError(reason2)
    
    # Two URLErrors with same reason are not equal (no __eq__ defined)
    # This is standard Python behavior for exceptions
    assert err1 != err2  # Different objects
    assert err1 is not err2
    
    # But they should have equal attributes
    assert err1.reason == err2.reason
    assert err1.args == err2.args

@given(st.text(), st.integers(100, 599), st.text())
def test_httperror_code_type_consistency(url, code, msg):
    """Test that HTTPError code is always an integer"""
    err = urllib.error.HTTPError(url, code, msg, {}, None)
    
    # code, status, and getcode() should all return the same integer
    assert err.code == code
    assert err.status == code
    assert err.getcode() == code
    
    # All should be integers
    assert isinstance(err.code, int)
    assert isinstance(err.status, int)
    assert isinstance(err.getcode(), int)

@given(st.text())
def test_urlerror_is_osserror(reason):
    """Test that URLError is properly an OSError subclass"""
    err = urllib.error.URLError(reason)
    
    # Should be an OSError
    assert isinstance(err, OSError)
    
    # Should be catchable as OSError
    try:
        raise err
    except OSError as e:
        assert e is err
    except:
        assert False, "Should have been caught as OSError"

@given(st.text(), st.integers(100, 599), st.text())
def test_httperror_dual_nature(url, code, msg):
    """Test HTTPError's dual nature as exception and response"""
    err = urllib.error.HTTPError(url, code, msg, {}, None)
    
    # Should be both an exception and have response-like methods
    assert isinstance(err, Exception)
    assert hasattr(err, 'read')  # File-like
    assert hasattr(err, 'getcode')  # Response-like
    assert hasattr(err, 'geturl')  # Response-like
    
    # Can be raised as exception
    try:
        raise err
    except urllib.error.HTTPError as e:
        assert e.code == code
    
    # Can be used as response object  
    assert err.getcode() == code
    assert err.geturl() == url

if __name__ == '__main__':
    import pytest
    import sys
    sys.exit(pytest.main([__file__, '-v']))