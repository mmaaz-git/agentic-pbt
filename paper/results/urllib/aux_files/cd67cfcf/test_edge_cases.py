#!/usr/bin/env python3
"""Test edge cases in urllib.error"""

import urllib.error
import io
from hypothesis import given, strategies as st

@given(st.binary())
def test_httperror_fp_handling(content):
    """Test HTTPError file pointer handling edge cases"""
    # When fp is provided
    fp = io.BytesIO(content)
    err = urllib.error.HTTPError('http://test.com', 404, 'Not Found', {}, fp)
    
    # The fp should be used as-is
    assert err.fp is fp
    
    # When fp is None
    err2 = urllib.error.HTTPError('http://test.com', 404, 'Not Found', {}, None)
    
    # Should create a BytesIO
    assert err2.fp is not None
    assert isinstance(err2.fp, io.BytesIO)
    
    # The created BytesIO should be empty
    assert err2.read() == b''

@given(st.text(), st.text())  
def test_httperror_headers_property_mutation(url, header_value):
    """Test that modifying headers property affects hdrs"""
    err = urllib.error.HTTPError(url, 404, 'Not Found', {}, None)
    
    # Initially both should be empty dict
    assert err.headers == {}
    assert err.hdrs == {}
    
    # Setting headers should update hdrs
    new_headers = {'X-Custom': header_value}
    err.headers = new_headers
    
    # Both should point to the same object
    assert err.headers is new_headers
    assert err.hdrs is new_headers
    
    # Modifying through hdrs should be visible through headers
    err.hdrs['Another'] = 'value'
    assert err.headers['Another'] == 'value'

@given(st.text())
def test_httperror_reason_property_immutable(new_msg):
    """Test that reason property cannot be set (it's a getter-only property)"""
    err = urllib.error.HTTPError('http://test.com', 404, 'Original', {}, None)
    
    # reason should equal msg
    assert err.reason == 'Original'
    
    # Changing msg should change reason
    err.msg = new_msg
    assert err.reason == new_msg
    
    # But we shouldn't be able to set reason directly
    try:
        err.reason = 'Cannot set this'
        assert False, "Should not be able to set reason property"
    except AttributeError:
        # This is expected - reason is read-only
        pass

@given(st.text(), st.binary())
def test_content_too_short_error_content_preservation(message, content):
    """Test that ContentTooShortError preserves content correctly"""
    err = urllib.error.ContentTooShortError(message, content)
    
    # Content should be preserved exactly
    assert err.content == content
    assert err.content is content  # Should be the same object
    
    # Reason should be the message
    assert err.reason == message
    
    # Should still have URLError properties
    assert isinstance(err, urllib.error.URLError)
    assert str(err).startswith('<urlopen error')

if __name__ == '__main__':
    import pytest
    import sys
    sys.exit(pytest.main([__file__, '-v']))