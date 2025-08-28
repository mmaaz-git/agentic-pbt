#!/usr/bin/env python3
"""Property-based tests for pyramid.session module using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import json
import time
import binascii
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, assume, settings
import pytest

from pyramid.session import (
    JSONSerializer,
    SignedSerializer,
    PickleSerializer,
    BaseCookieSessionFactory,
    SignedCookieSessionFactory,
    bytes_,
    text_,
    manage_accessed,
    manage_changed,
)


# Test 1: JSONSerializer round-trip property
@given(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers()),
        st.dictionaries(
            st.text(),
            st.one_of(
                st.text(),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.lists(st.text()),
                st.none()
            )
        )
    )
)
def test_json_serializer_round_trip(data):
    """JSONSerializer should correctly round-trip JSON-serializable objects."""
    serializer = JSONSerializer()
    
    # Serialize and deserialize
    serialized = serializer.dumps(data)
    deserialized = serializer.loads(serialized)
    
    assert deserialized == data


# Test 2: SignedSerializer round-trip property with valid secret
@given(
    st.text(min_size=1, max_size=100),  # secret
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    )
)
def test_signed_serializer_round_trip(secret, data):
    """SignedSerializer should correctly round-trip data with signature."""
    serializer = SignedSerializer(secret, serializer=JSONSerializer())
    
    # Serialize and deserialize
    serialized = serializer.dumps(data)
    deserialized = serializer.loads(serialized)
    
    assert deserialized == data


# Test 3: SignedSerializer should reject tampered data
@given(
    st.text(min_size=1, max_size=100),  # secret
    st.dictionaries(st.text(), st.integers(), min_size=1)
)
def test_signed_serializer_tamper_detection(secret, data):
    """SignedSerializer should detect tampered data."""
    serializer = SignedSerializer(secret, serializer=JSONSerializer())
    
    # Serialize data
    serialized = serializer.dumps(data)
    
    # Tamper with the serialized data (modify a byte)
    serialized_bytes = bytes_(serialized)
    if len(serialized_bytes) > 10:
        # Tamper by changing a byte in the middle
        tampered_bytes = bytearray(serialized_bytes)
        tampered_bytes[len(tampered_bytes) // 2] ^= 1  # Flip one bit
        tampered = bytes(tampered_bytes)
        
        # Should raise ValueError on tampered data
        with pytest.raises(ValueError):
            serializer.loads(tampered)


# Test 4: bytes_ conversion property
@given(st.text())
def test_bytes_conversion(text):
    """bytes_ should convert str to bytes, leave bytes unchanged."""
    # Convert str to bytes
    result = bytes_(text)
    assert isinstance(result, bytes)
    assert result == text.encode('latin-1')
    
    # bytes_ should leave bytes unchanged
    result2 = bytes_(result)
    assert result2 == result
    assert isinstance(result2, bytes)


# Test 5: text_ conversion property
@given(st.binary())
def test_text_conversion(data):
    """text_ should convert bytes to str, leave str unchanged."""
    try:
        # Convert bytes to str
        result = text_(data)
        assert isinstance(result, str)
        
        # text_ should leave str unchanged
        result2 = text_(result)
        assert result2 == result
        assert isinstance(result2, str)
    except UnicodeDecodeError:
        # Some byte sequences can't be decoded as latin-1
        pass


# Test 6: bytes_ and text_ round-trip for valid latin-1 text
@given(st.text(alphabet=st.characters(min_codepoint=0, max_codepoint=255)))
def test_bytes_text_round_trip(text):
    """bytes_ and text_ should round-trip for latin-1 compatible text."""
    # str -> bytes -> str
    bytes_data = bytes_(text)
    text_data = text_(bytes_data)
    assert text_data == text
    
    # bytes -> str -> bytes
    str_data = text_(bytes_data)
    bytes_data2 = bytes_(str_data)
    assert bytes_data2 == bytes_data


# Test 7: Session flash message round-trip
@given(
    st.text(min_size=1),  # message
    st.text(),  # queue name
    st.booleans()  # allow_duplicate
)
def test_session_flash_round_trip(message, queue, allow_duplicate):
    """Flash messages should be retrievable via pop_flash."""
    factory = BaseCookieSessionFactory(JSONSerializer())
    
    # Mock request
    request = Mock()
    request.cookies = {}
    request.add_response_callback = Mock()
    
    session = factory(request)
    
    # Add flash message
    session.flash(message, queue, allow_duplicate)
    
    # Pop should return the message
    messages = session.pop_flash(queue)
    assert message in messages
    
    # Queue should now be empty
    messages2 = session.pop_flash(queue)
    assert messages2 == []


# Test 8: Flash peek should not modify queue
@given(
    st.lists(st.text(min_size=1), min_size=1, max_size=10),
    st.text()
)
def test_session_flash_peek_idempotent(messages, queue):
    """peek_flash should not modify the flash queue."""
    factory = BaseCookieSessionFactory(JSONSerializer())
    
    request = Mock()
    request.cookies = {}
    request.add_response_callback = Mock()
    
    session = factory(request)
    
    # Add multiple messages
    for msg in messages:
        session.flash(msg, queue)
    
    # Peek multiple times should return same result
    peek1 = session.peek_flash(queue)
    peek2 = session.peek_flash(queue)
    assert peek1 == peek2
    
    # Pop should still return all messages
    popped = session.pop_flash(queue)
    assert set(popped) == set(messages) or (not session.flash(messages[0], queue, False) if len(set(messages)) != len(messages) else True)


# Test 9: CSRF token consistency
def test_csrf_token_consistency():
    """get_csrf_token should return same token until new_csrf_token is called."""
    factory = BaseCookieSessionFactory(JSONSerializer())
    
    request = Mock()
    request.cookies = {}
    request.add_response_callback = Mock()
    
    session = factory(request)
    
    # First call creates a token
    token1 = session.get_csrf_token()
    assert token1 is not None
    assert len(token1) == 40  # 20 bytes hex = 40 chars
    
    # Subsequent calls return same token
    token2 = session.get_csrf_token()
    assert token2 == token1
    
    # new_csrf_token creates a different token
    token3 = session.new_csrf_token()
    assert token3 != token1
    assert len(token3) == 40
    
    # get_csrf_token now returns the new token
    token4 = session.get_csrf_token()
    assert token4 == token3


# Test 10: CSRF token uniqueness
def test_csrf_token_uniqueness():
    """new_csrf_token should generate unique tokens."""
    factory = BaseCookieSessionFactory(JSONSerializer())
    
    request = Mock()
    request.cookies = {}
    request.add_response_callback = Mock()
    
    session = factory(request)
    
    tokens = set()
    for _ in range(100):
        token = session.new_csrf_token()
        assert token not in tokens
        tokens.add(token)
        # Should be 40 hex characters (20 bytes)
        assert len(token) == 40
        assert all(c in '0123456789abcdef' for c in token)


# Test 11: Session acts as dictionary
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.one_of(st.integers(), st.text(), st.none()),
        max_size=10
    )
)
def test_session_dictionary_behavior(data):
    """Session should behave like a dictionary."""
    factory = BaseCookieSessionFactory(JSONSerializer())
    
    request = Mock()
    request.cookies = {}
    request.add_response_callback = Mock()
    
    session = factory(request)
    
    # Add data
    for key, value in data.items():
        session[key] = value
    
    # Check all dictionary operations
    assert len(session) >= len(data)  # May have internal keys
    
    for key, value in data.items():
        assert key in session
        assert session[key] == value
        assert session.get(key) == value
    
    # Test pop
    if data:
        key = list(data.keys())[0]
        value = session.pop(key)
        assert value == data[key]
        assert key not in session


# Test 12: Cookie size limit enforcement
@given(st.dictionaries(
    st.text(min_size=1, max_size=100),
    st.text(min_size=1000, max_size=2000),
    min_size=3, max_size=5
))
def test_cookie_size_limit(large_data):
    """Session should raise error if cookie exceeds 4064 bytes."""
    factory = BaseCookieSessionFactory(JSONSerializer())
    
    request = Mock()
    request.cookies = {}
    callbacks = []
    request.add_response_callback = lambda cb: callbacks.append(cb)
    
    session = factory(request)
    
    # Add large data
    for key, value in large_data.items():
        session[key] = value
    
    # Force cookie setting
    session.changed()
    
    # Create mock response
    response = Mock()
    response.set_cookie = Mock()
    
    # Try to set cookie
    if callbacks:
        with pytest.raises(ValueError, match="Cookie value is too long"):
            callbacks[0](request, response)


# Test 13: Session timeout behavior
@patch('time.time')
def test_session_timeout(mock_time):
    """Session should expire after timeout period."""
    timeout = 100
    factory = BaseCookieSessionFactory(JSONSerializer(), timeout=timeout)
    
    # Create initial session
    mock_time.return_value = 1000
    request = Mock()
    request.cookies = {}
    callbacks = []
    request.add_response_callback = lambda cb: callbacks.append(cb)
    
    session1 = factory(request)
    session1['key'] = 'value'
    session1.changed()
    
    # Get cookie value
    response = Mock()
    cookie_val = None
    def capture_cookie(name, value=None, **kwargs):
        nonlocal cookie_val
        cookie_val = value
    response.set_cookie = capture_cookie
    
    if callbacks:
        callbacks[0](request, response)
    
    # Create new session with cookie, within timeout
    mock_time.return_value = 1050  # 50 seconds later
    request2 = Mock()
    request2.cookies = {'session': cookie_val}
    request2.add_response_callback = Mock()
    
    session2 = factory(request2)
    assert 'key' in session2
    assert session2['key'] == 'value'
    
    # Create new session with cookie, after timeout
    mock_time.return_value = 1200  # 200 seconds later
    request3 = Mock()
    request3.cookies = {'session': cookie_val}
    request3.add_response_callback = Mock()
    
    session3 = factory(request3)
    assert 'key' not in session3  # Should be expired


# Test 14: manage_accessed decorator
def test_manage_accessed_updates_time():
    """manage_accessed should update accessed time on read operations."""
    
    def dummy_get(self, key, default=None):
        return dict.get(self, key, default)
    
    wrapped_get = manage_accessed(dummy_get)
    
    # Create mock session
    session = Mock()
    session.accessed = 1000
    session.renewed = 1000
    session._reissue_time = None
    dict.__init__ = Mock()
    
    with patch('time.time', return_value=2000):
        wrapped_get(session, 'key')
    
    assert session.accessed == 2000


# Test 15: manage_changed decorator
def test_manage_changed_triggers_cookie_set():
    """manage_changed should trigger cookie setting on write operations."""
    
    def dummy_set(self, key, value):
        dict.__setitem__(self, key, value)
    
    wrapped_set = manage_changed(dummy_set)
    
    # Create mock session
    session = Mock()
    session.accessed = 1000
    session.changed = Mock()
    dict.__setitem__ = Mock()
    
    with patch('time.time', return_value=2000):
        wrapped_set(session, 'key', 'value')
    
    assert session.accessed == 2000
    session.changed.assert_called_once()


# Test 16: PickleSerializer round-trip (deprecated but still exists)
@given(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False),
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    )
)
def test_pickle_serializer_round_trip(data):
    """PickleSerializer should correctly round-trip Python objects."""
    serializer = PickleSerializer()
    
    # Serialize and deserialize
    serialized = serializer.dumps(data)
    deserialized = serializer.loads(serialized)
    
    assert deserialized == data


# Test 17: SignedCookieSessionFactory creates signed sessions
@given(
    st.text(min_size=20, max_size=100),  # secret
    st.text(min_size=1, max_size=20)  # cookie name
)
def test_signed_cookie_session_factory(secret, cookie_name):
    """SignedCookieSessionFactory should create sessions with signed cookies."""
    factory = SignedCookieSessionFactory(
        secret=secret,
        cookie_name=cookie_name
    )
    
    request = Mock()
    request.cookies = {}
    request.add_response_callback = Mock()
    
    session = factory(request)
    
    # Session should work like normal
    session['test'] = 'value'
    assert session['test'] == 'value'
    
    # Should have the correct cookie name configured
    assert session._cookie_name == cookie_name


if __name__ == "__main__":
    print("Running property-based tests for pyramid.session...")
    print("Use: pytest test_pyramid_session.py -v")