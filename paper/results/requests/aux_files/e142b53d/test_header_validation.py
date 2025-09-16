"""Investigate header validation behavior in requests."""

from hypothesis import given, strategies as st, settings
from requests import Request, Session
from requests.exceptions import InvalidHeader
import string


# Test what characters are allowed in header names
@given(st.text(min_size=1, max_size=10))
@settings(max_examples=1000)
def test_header_name_validation(header_name):
    """Test which header names are accepted vs rejected."""
    session = Session()
    req = Request('GET', 'http://example.com', headers={header_name: 'value'})
    
    try:
        prep = session.prepare_request(req)
        # If it succeeds, header should not contain control chars
        assert '\r' not in header_name
        assert '\n' not in header_name
        assert '\x00' not in header_name
        # Also shouldn't have leading/trailing whitespace
        assert header_name == header_name.strip()
    except InvalidHeader:
        # Should only reject headers with control chars or whitespace issues
        assert (
            '\r' in header_name or 
            '\n' in header_name or
            '\x00' in header_name or
            header_name != header_name.strip() or
            header_name.startswith(' ') or
            header_name.endswith(' ') or
            ':' in header_name or
            not header_name
        )


# Test header value validation
@given(st.text())
@settings(max_examples=1000)
def test_header_value_validation(header_value):
    """Test which header values are accepted vs rejected."""
    session = Session()
    req = Request('GET', 'http://example.com', headers={'X-Test': header_value})
    
    try:
        prep = session.prepare_request(req)
        # If it succeeds, value should not contain certain control chars
        assert '\r' not in header_value or '\n' not in header_value
    except (InvalidHeader, UnicodeError):
        # Should reject values with control characters
        pass


# Test that Session.headers accepts invalid headers but fails on prepare
@given(
    st.dictionaries(
        st.text(min_size=1),
        st.text(),
        min_size=1
    )
)
@settings(max_examples=500)
def test_session_deferred_header_validation(headers):
    """Test that invalid headers are accepted but fail on prepare."""
    session = Session()
    
    # This should always succeed - no validation yet
    session.headers.update(headers)
    assert all(key in session.headers for key in headers)
    
    # But preparing a request might fail if headers are invalid
    req = Request('GET', 'http://example.com')
    try:
        prep = session.prepare_request(req)
        # If this succeeds, all headers must be valid
        for key in headers:
            assert '\r' not in key and '\n' not in key
    except InvalidHeader:
        # At least one header must be invalid
        assert any('\r' in key or '\n' in key or ':' in key 
                  or key != key.strip() 
                  for key in headers)